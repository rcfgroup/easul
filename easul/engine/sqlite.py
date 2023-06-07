import itertools
import operator
import sqlite3

from easul.engine.db import SqliteDb, ClientBatchedSqliteDb, BrokerBatchedSqliteDb
from easul.engine import Client, JsonCodec, LOG, Broker
import datetime as dt

from easul.outcome import FailedOutcome


class SqliteClient(Client):
    """
    Client which uses SQLite as its basis.
    """
    codec = JsonCodec

    def __init__(self, db_file):
        self.db = SqliteDb(db_file)
        self._create_tables()

    def _create_tables(self):
        if self.db.does_table_exist("journey") is False:
            self.db.create_table_from_values("journey", {"reference":"","source":"","label":"","complete":0}, has_id_field=True, indexes={"journey_reference_idx":"reference"})

        if self.db.does_table_exist("state") is False:
            self.db.create_table_from_values("state", {"journey":0, "label":"","state":"", "reason":"", "from_step":""}, has_id_field=True,indexes={"state_journey_idx":"journey"})

        if self.db.does_table_exist("step") is False:
            self.db.create_table_from_values("step", {"journey": 0, "name": "", "status": "", "status_info": "",
                  "reason": "", "value": "", "result": "",
                  "outcome": "", "next_step": "","timestamp":""}, has_id_field=True,indexes={"step_journey_idx":"journey"})

    def create_journey(self, reference, source, label=None):
        values = {"reference":str(reference),"source":source,"label":label,"complete":0}
        return self.db.insert_row("journey",values)

    def get_journey(self, reference, source):
        values = {"reference":reference}
        LOG.warning("get_journey values:{values}")
        return self.db.get_row("journey", values)

    def set_current_state(self, state_label, state, journey_id=None, reference=None, reason=None, from_step=None, timestamp=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        values = {"journey":journey_id, "label":state_label,"state":state, "reason":reason, "from_step":from_step}

        if timestamp:
            values["timestamp"] = timestamp

        return self.db.insert_row("state", values)

    def set_current_step(self, step_name, status, status_info=None, journey_id=None, reference=None, outcome=None, timestamp=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        if outcome and issubclass(outcome.__class__, FailedOutcome) is False:
            value = str(outcome.get("result",{}).get("value"))
            result = str(outcome.get("result"))
            values = {"journey": journey_id, "name": step_name, "status": status, "status_info":status_info, "reason":outcome.get("reason"), "value":value, "result": result, "outcome": self.codec.encode(outcome), "next_step":outcome.get("next_step"), "timestamp":timestamp }
        else:
            values = {"journey": journey_id, "name": step_name, "status": status, "status_info": status_info,
                  "reason": "", "value": "", "result": "",
                  "outcome": "", "next_step": "","timestamp":timestamp}

        steps = self.db.get_rows("step",{"journey":journey_id, "name":step_name, "timestamp":timestamp})

        if len(steps) > 0:
            c_step = steps[-1]
            c_status = c_step["status"]

            if c_status == status:
                if status!="READY":
                    return None

            return self.db.update_row("step", c_step, values)

        return self.db.insert_row("step", values)

    def get_current_state(self, state_label, journey_id=None, reference=None, timestamp=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        state_log = self.db.get_rows("state", {"journey":journey_id, "label":state_label, "timestamp":(timestamp, operator.le)}, order_by=["-timestamp","-id"])
        sorted_state_log = sorted(state_log, key=lambda x: x["timestamp"], reverse=True)

        return sorted_state_log[0] if len(sorted_state_log)>0 else None

    def get_current_states(self, journey_id=None, reference=None):
        if reference:
            journey = self.get_journey(reference=reference)
            journey_id = journey['id']

        states = self.db.get_rows("state", {"journey": journey_id})

        states_by_label = itertools.groupby(states, lambda x: x["label"])

        current_states = {}

        for label, states in states_by_label:
            sorted_states = sorted(states, key=lambda x: x["timestamp"] if x.get("timestamp") else dt.datetime.min, reverse=True)
            current_states[label] = sorted_states[0]

        return current_states

    def get_all_states(self, journey_id=None, reference=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        return self.db.get_rows("state", {"journey": journey_id})

    def get_step(self, step_name, journey_id=None, reference=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        try:
            rows = self.db.get_rows("step", {"name":step_name, "journey": journey_id})
            return None if len(rows)==0 else rows[0]
        except sqlite3.OperationalError:
            return None

    def get_steps(self, journey_id=None, reference=None):
        if reference:
            journey = self.get_journey(reference)
            journey_id = journey['id']

        try:
            return self.db.get_rows("step", {"journey": journey_id}, )
        except sqlite3.OperationalError:
            return []

    def get_latest_step(self, journey_id=None, reference=None):
        steps = self.get_steps(journey_id=journey_id, reference=reference)

        if len(steps) == 0:
            return None

        return steps[-1]

    def get_step_route(self, journey_id):
        steps = self.get_steps(journey_id=journey_id)

        route = []

        steps = sorted(steps, key=lambda x: x["timestamp"])

        for step in steps:
            if step["name"] in route:
                continue

            route.append(step["name"])

        return route

    def complete_journey(self, journey_id=None, reference=None):
        if journey_id is None:
            existing = self.get_journey(reference=reference)
            journey_id = existing["id"]

        self.db.update_row("journey",{"id":journey_id}, {"complete":1})

    def get_journeys(self):
        return self.db.get_rows("journey")

    def get_journey(self, id=None, reference=None, source="admissions"):
        if id:
            return self.db.get_row("journey",{"id":id})

        return self.db.get_row("journey",{"reference":reference})


class BatchedSqliteClient(SqliteClient):
    def __init__(self, db_file, batch_size):
        self.db = ClientBatchedSqliteDb(SqliteDb(db_file), batch_size)
        self.batch_size = batch_size
        self._create_tables()

class SqliteBroker(Broker):
    """
    Broker which uses Sqlite as its basis.
    """
    DATA_STORE_TABLE = "data_store"

    def __init__(self, db_file):
        self.db = SqliteDb(db_file)
        self._create_tables()

    def _create_tables(self):
        if self.db.does_table_exist("data_store") is False:
            self.db.create_table_from_values("data_store", {"ref":"", "data_type":"", "data":"", "external":""}, has_id_field=True, indexes={"data_store_ref_idx":"ref, data_type"})


    def store_data(self, reference, data_type, data, external=False, send_message=False):
        row = {"ref":reference, "data_type":data_type, "data":self.codec.encode(data), "external":external}
        self.db.insert_row("data_store", row)

    def retrieve_data(self, reference, data_type):
        row = self.db.get_row(self.DATA_STORE_TABLE, {"ref":reference, "data_type":data_type})
        return self.codec.decode(row.get("data"))

    def new_pubsub(self, *args, **kwargs):
        return self.client.pubsub(*args, **kwargs)


    def create_channel(self, channel_name, channel_callback=None):
        pubsub = self.client.pubsub(ignore_subscribe_messages=True)

        if channel_callback:
            pubsub.subscribe(**{channel_name: self._channel_wrapper(channel_callback)})

        return pubsub


    def _channel_wrapper(self, channel_callback):
        def _internal(msg):
            if not msg:
                return None

            msg = self.decode_message(msg)

            return channel_callback(msg, self)

        return _internal


class BatchedSqliteBroker(SqliteBroker):
    """
    Broker which uses a batched SQLite approach as its basis
    """
    def __init__(self, db_file, batch_size):
        self.db = BrokerBatchedSqliteDb(SqliteDb(db_file), batch_size)
        self.batch_size = batch_size
        self._create_tables()