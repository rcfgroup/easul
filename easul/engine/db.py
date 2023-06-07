import operator
import sqlite3
from typing import Any

from pandas import Timestamp
import datetime as dt
import logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
from abc import abstractmethod

class SqliteDb:
    """
    SQliteDb wrapper which provides helper functions for creating tables and dealing with rows.
    """
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, isolation_level="IMMEDIATE")
        self.conn.row_factory = SqliteDb._dict_factory
        sqlite3.register_adapter(dt.time, SqliteDb._adapt_time)
        sqlite3.register_adapter(Timestamp, SqliteDb._adapt_timestamp)
        self.existing_tables = {}

    @staticmethod
    def _adapt_time(t):
        return t.strftime("%H:%M:%S")

    @staticmethod
    def _adapt_timestamp(ts: Timestamp):
        return ts.isoformat()

    @staticmethod
    def _dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def does_table_exist(self, table_name):
        if table_name not in self.existing_tables:
            self.existing_tables[table_name] = self.has_row("sqlite_master", {"type": "table", "name": table_name})

        return self.existing_tables[table_name]

    def create_table_from_values(self, table_name, values, has_id_field=False, indexes=None):
        if not indexes:
            indexes = {}

        create_fields = []

        if has_id_field:
            create_fields.append("id INTEGER PRIMARY KEY AUTOINCREMENT")

        create_fields.append("timestamp DATETIME NULL")

        for field, value in values.items():
            if field == "id" or field == "timestamp":
                continue

            if isinstance(value, dt.datetime) or isinstance(value, Timestamp):
                create_fields.append(f"{field} DATETIME")
            elif isinstance(value, dt.date):
                create_fields.append(f"{field} DATE")
            elif isinstance(value, dt.time):
                create_fields.append(f"{field} TIME")
            elif isinstance(value, int) or isinstance(value, float):
                create_fields.append(f"{field} DOUBLE")
            else:
                create_fields.append(f"{field} TEXT")

        sql = f"CREATE TABLE '{table_name}' (" + ",".join(create_fields) + ")"
        self.conn.execute(sql)

        for idx_name, idx_fields in indexes.items():
            self.conn.execute(f"CREATE INDEX {idx_name} ON '{table_name}' ({idx_fields})")

        self.existing_tables[table_name] = True

    def has_row(self, table_name, values):
        curs = self.conn.cursor()
        where, params = self._create_where(values)
        sql = f"select count(*) as row_count from '{table_name}' where " + where
        curs.execute(sql, params)
        row = curs.fetchone()
        curs.close()
        return True if row['row_count'] > 0 else False

    def get_row(self, table_name, values):
        try:
            curs = self._select_cursor(table_name, values)
            row = curs.fetchone()
            curs.close()
            return row
        except sqlite3.OperationalError as ex:
            import re

            if re.match("no such table", str(ex)):
                return None

            raise ex

    def _select_cursor(self, table_name, values, order_by=None):
        where, params = self._create_where(values)
        if where:
            where =  " where " + where


        if order_by:
            order_list = []
            for order_item in order_by:
                if order_item[0] == "-":
                    order_list.append(order_item[1:] + " DESC")
                else:
                    order_list.append(order_item + " ASC")
            order_by_str = " ORDER BY " + ",".join(order_list)
        else:
            order_by_str = ""

        sql = f"select * from '{table_name}'" + where + order_by_str

        return self.create_cursor(sql, params)

    def create_cursor(self, sql, values=None):
        curs = self.conn.cursor()

        curs.execute(sql, values if values else {})
        return curs

    def get_rows_with_sql(self, sql, values):
        curs = self.create_cursor(sql, values)
        rows = curs.fetchall()
        curs.close()
        return rows

    def get_rows(self, table_name, values=None, order_by=None):
        curs = self._select_cursor(table_name, values, order_by=order_by)
        rows = curs.fetchall()
        curs.close()
        return rows

    def insert_rows(self, table_name, rows):
        if len(rows)==0:
            LOG.warning("No rows to insert")
            return

        fields = list(rows[0].keys())
        sql = self._get_insert_sql(table_name, fields)

        curs = self.conn.cursor()
        curs.executemany(sql, rows)
        curs.close()

        self.conn.commit()

    def _get_insert_sql(self, table_name, fields):
        placeholders = [":" + f for f in fields]
        return f"INSERT INTO '{table_name}' ({','.join(fields)}) VALUES({','.join(placeholders)})"

    def insert_row(self, table_name, values, update_id=True):
        fields = list(values.keys())

        sql = self._get_insert_sql(table_name, fields)
        curs = self.conn.cursor()
        curs.execute(sql, values)

        if update_id:
            curs.execute(f"SELECT last_insert_rowid() as last_id FROM '{table_name}'")
            row = curs.fetchone()
            values["id"] = row["last_id"]

        curs.close()
        self.conn.commit()

        return values

    def update_row(self, table_name, old_values, new_values):
        if "id" in old_values:
            old_values = {"id": old_values['id']}

        params = {f"{k}": v for k, v in old_values.items()}

        where, sel_params = self._create_where(old_values)

        placeholders = [f + "=:" + f for f in new_values.keys()]
        params.update(new_values)

        sql = f"UPDATE '{table_name}' SET {','.join(placeholders)} WHERE {where}"

        curs = self.create_cursor(sql, params)
        curs.close()

        if "id" in old_values:
            new_values["id"] = old_values["id"]

        self.conn.commit()
        return new_values

    def _create_where(self, fields):
        if not fields:
            return "", {}

        import operator
        clauses = []
        params = {}
        for k,v in fields.items():
            op_str = "="
            if isinstance(v, tuple):
                if v[1]==operator.le:
                    op_str = "<="
                    params[k] = v[0]
            else:
                params[k] = v

            clauses.append(f"{k} {op_str} :{k}")

        return " AND ".join(clauses), params


class BatchedSqliteDb:
    """
    Decorator for SQLiteDb with support for batching of rows. Data is stored in data structures until it reaches a certain number of
    rows. At which point it is persisted to the SQLite DB
    """
    def __init__(self, db:SqliteDb, batch_size:int=1000):
        self._db = db
        self._batch_size=batch_size
        self._reset_tables()

    @abstractmethod
    def _reset_tables(self):
        pass

    def does_table_exist(self, table_name):
        return self._db.does_table_exist(table_name)

    def create_table_from_values(self, table_name, values, has_id_field=False, indexes=None):
        if not indexes:
            indexes = []

        # self._table_defs[table_name]={"values":values,"has_id_field":has_id_field, "indexes":indexes}

        self._db.create_table_from_values(table_name, values, has_id_field=has_id_field, indexes=indexes)

    def _filter_data(self, table_name, matches):
        match_value_ops = []
        for match_key, match_value in matches.items():
            if type(match_value) is tuple:
                match_value_ops.append((match_key,) + match_value)
            else:
                match_value_ops.append((match_key, match_value, operator.eq))

        def _match_fn(data):
            for match_key, match_value, match_op in match_value_ops:
                if match_op(data.get(match_key), match_value) is False:
                    return False

            return True

        return list(filter(_match_fn, self._tables[table_name]))

    def has_row(self, table_name:str, values:Any):
        return True if len(self._filter_data(table_name, values))>0 else False

    def get_row(self, table_name, values):
        rows = self.get_rows(table_name, values)
        if len(rows)==0:
            return None

        return rows[0]

    def _get_sort_key(self, item_key, sort_row):
        import operator

        if item_key[0] == "-":
            return operator.neg(sort_row[item_key[1:]])

        return sort_row[item_key]

    def get_rows(self, table_name, values=None, order_by=None):
        data = self._filter_data(table_name, values)

        if order_by:
            for order_item in order_by:
                reverse = False
                if order_item[0] == "-":
                    order_item = order_item[1:]
                    reverse = True

                data = sorted(data, key=lambda x: x[order_item], reverse=reverse)

        return data

    def insert_row(self, table_name, values):
        if self._do_persist(table_name, values):
            self._persist_batch()

        values["id"] = len(self._tables[table_name])

        if "timestamp" not in values:
            values["timestamp"] = dt.datetime.now().isoformat()

        self._tables[table_name].append(values)


        return values

    def update_row(self, table_name, old_values, new_values):
        if "id" in old_values:
            old_values = {"id": old_values['id']}

        old_rows = self._filter_data(table_name,old_values)

        for old_row in old_rows:
            self._tables[table_name][old_row['id']].update(new_values)

        if "id" in old_values:
            new_values["id"] = old_values["id"]

        return new_values

    @abstractmethod
    def _do_persist(self, table_name, new_values):
        pass

    @abstractmethod
    def _persist_batch(self):
        pass

    def __del__(self):
        self._persist_batch()
        
class ClientBatchedSqliteDb(BatchedSqliteDb):
    """
    BatchedSqliteDb tailored to client support.
    """
    def _reset_tables(self):
        self._tables = {"journey": [], "step": [], "state": []}

    def _do_persist(self, table_name, new_values):
        return table_name == "journey" and len(
            self._tables["journey"]) >= self._batch_size

    def _persist_batch(self):
        LOG.info(f"Persisting {len(self._tables['journey'])} journeys")
        journey_map = {}
        for idx, jvalues in enumerate(self._tables["journey"]):
            del (jvalues["id"])
            journey = self._db.insert_row("journey", jvalues)
            journey_map[idx] = journey['id']

        states = []
        LOG.info(f"Persisting {len(self._tables['state'])} states")

        for idx, svalues in enumerate(self._tables["state"]):
            del (svalues["id"])
            svalues["journey"] = journey_map[svalues["journey"]]
            states.append(svalues)

        self._db.insert_rows("state", states)

        steps = []

        LOG.info(f"Persisting {len(self._tables['step'])} steps")

        for idx, svalues in enumerate(self._tables["step"]):
            del (svalues["id"])
            svalues["journey"] = journey_map[svalues["journey"]]
            steps.append(svalues)

        self._db.insert_rows("step", steps)

        self._reset_tables()


class BrokerBatchedSqliteDb(BatchedSqliteDb):
    """
    BatchedSqliteDb tailored to broker support.
    """
    def _reset_tables(self):
        self._tables = {"data_store": []}
        self._journeys = {}

    def _do_persist(self, table_name, new_values):
        return len(self._journeys) >= self._batch_size

    def _persist_batch(self):
        LOG.info(f"Persisting {len(self._tables['data_store'])} data_stores")

        for idx, dvalues in enumerate(self._tables["data_store"]):
            del (dvalues["id"])
            self._db.insert_row("data_store", dvalues)

        self._reset_tables()

    def insert_row(self, table_name, values):
        if values["ref"] not in self._journeys:
            self._journeys[values["ref"]] = True

        super().insert_row(table_name, values)


