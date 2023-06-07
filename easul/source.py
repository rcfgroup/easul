import pandas as pd
from typing import List, Any, Dict

from easul.error import StepDataNotAvailable

import logging

from abc import abstractmethod
from attrs import define, field
from functools import partial

from easul.util import get_current_result
LOG = logging.getLogger(__name__)

@define(kw_only=True)
class Source:
    """
    Base Source class. Sources provide access to raw data and processing which enables the creation of validated
    InputData - which can be fed into algorithms.
    """
    title: str = field()
    processes = field(factory=list)

    def retrieve(self, driver, step):
        """
        Retrieve data in the form of a Python data structure.
        Args:
            driver:
            step:

        Returns:

        """
        data = self._retrieve_final_data(driver, step)

        if not data:
            raise StepDataNotAvailable(driver.journey, step.name, retry=False, source_title=self.title)

        return data

    def _retrieve_final_data(self, driver, step):
        raw_data = self._retrieve_raw_data(driver, step)
        return self._process_raw_data(raw_data)

    @abstractmethod
    def _retrieve_raw_data(self, driver, step):
        pass

    @property
    def source_titles(self):
        return [self.title]

    def describe(self):
        return {
            "title":self.title,
            "type":self.__class__.__name__,
        }

    def _process_raw_data(self, raw_data):
        if raw_data is None:
            raw_data = {}

        for process in self.processes:
            raw_data = process(raw_data)

        return raw_data

@define(kw_only=True)
class CollatedSource(Source):
    """
    Source which collates multiple sources into a single data output. If one source does not have data available the
    whole thing will throw a StepDataNotAvailable. This source is useful for combining data from disparate sources
    e.g. states, databases and messaging

    """
    sources: Dict[str,Source] = field(factory=list)

    def _retrieve_raw_data(self, driver, step):
        final_data = {}
        for source_name, source in self.sources.items():
            try:
                data = source.retrieve(driver, step)
            except StepDataNotAvailable as ex:
                LOG.warning(f"[{driver.journey.get('reference')}:{step.name}] Data from sub-source '{source.title}' not found")
                raise ex

            if type(data) is not dict:
                data = {"data":data}

            final_data.update(data)

        return final_data

@define(kw_only=True)
class BrokerSource(Source):
    """
    Source which retrieves data from the broker for the defined 'data_type'.
    """
    data_source:str = field()
    data_type:str = field()

    def _retrieve_raw_data(self, driver, step):
        data = driver.get_broker_data(self.data_type)

        if not data:
            raise StepDataNotAvailable(driver.journey, step.name, retry=False)

        return data



@define(kw_only=True)
class DbSource(Source):
    """
    Source which retrieves data from a database. Currently only supports SQLite.
    """
    db:str = field()
    table_name:str = field(default=None)
    sql:str = field(default=None)
    reference_field:str = field()
    multiple_rows = field(default=False)
    _cache = field(factory=dict)
    _data_fn = field()

    def __attrs_post_init__(self):
        if self.table_name is None and self.sql is None:
            raise AttributeError("You must specify 'table_name' or 'sql'")

    @_data_fn.default
    def _default_data_fn(self):
        if self.table_name:
            return partial(self.db.get_rows, table_name=self.table_name)
        else:
            return partial(self.db.get_rows_with_sql, sql=self.sql)

    def _get_parameters(self, driver):
        return {self.reference_field:driver.journey["reference"]}

    def _retrieve_final_data(self, driver, step):
        if driver.journey["reference"] in self._cache:
            return self._cache[driver.journey["reference"]]

        data = super()._retrieve_final_data(driver, step)

        self._cache[driver.journey["reference"]] = data
        
        return data

    def _retrieve_raw_data(self, driver, step):
        params = self._get_parameters(driver)

        data = self._data_fn(values=params)
        if self.multiple_rows is False and type(data) is list:
            return data[0] if len(data) > 0 else None

        return data

@define(kw_only=True)
class TimebasedDbSource(DbSource):
    """
    Time-based DB source which introduces a timestamp_field which it uses with a Clock to retrieve data.
    """
    timestamp_field:str = field(default=None)
    default_values = field(default=None)
    sort_field = field(default=None)
    reverse_sort = field(default=False)

    def _get_parameters(self, driver):
        return {self.reference_field: driver.journey["reference"]}

    def _retrieve_final_data(self, driver, step):
        data = super()._retrieve_final_data(driver, step)

        res = get_current_result(data, driver.clock.timestamp, self.timestamp_field, self.sort_field, self.reverse_sort)
        return res



@define(kw_only=True)
class ConstantSource(Source):
    """
    Simple source which returns constant data. It does not differentiate between specific journeys
    (to do this you can use a StaticSource).
    """
    data:Any = field()

    def retrieve(self, driver, step):
        return self.data

@define(kw_only=True)
class StateSource(Source):
    """
    Source which uses the client to get a specific current 'state' and puts it in the 'output_field'.
    """
    state = field()
    output_field = field()

    def _retrieve_final_data(self, driver, step):
        state = driver._client.get_current_state(state_label=self.state.label, journey_id=driver.journey_id, timestamp=driver.clock.timestamp)
        if not state:
            return None
        data = { self.output_field : state["status"]}
        return data

@define(kw_only=True)
class StepResultSource(Source):
    """
    Source which returns the result from a previous step.
    """
    output_field = field()
    result_step_name = field()

    def retrieve(self, driver, step):
        step = driver._client.get_step(step_name=self.result_step_name, journey_id=driver.journey_id)
        data = {self.output_field: step["value"]}

        return data

@define(kw_only=True)
class StaticSource(Source):
    """
    Source which gets data from a 'source_data' property which contains specific journey data.
    The data is supplied as a dictionary:

    source_data = {
        "JOURNEY_REF_1": {"x1":1, "x2":2, "x3":3},
        "JOURNEY_REF_2": {"x1":2, "x2":4, "x3":6}
    }

    e.g.
    """
    source_data = field(factory=dict)

    def _retrieve_raw_data(self, driver, step):
        if driver.journey["reference"] not in self.source_data:
            raise StepDataNotAvailable(journey=driver.journey, step_name = step.name)

        return self.source_data.get(driver.journey["reference"])

@define(kw_only=True)
class DataFrameSource(Source):
    """
    Source which gets 'data' from a pandas DataFrame utilising an appropriate 'reference_field'.
    Also can use optional 'timestamp_field' if temporal in nature.
    """
    data:pd.DataFrame = field(factory=pd.DataFrame)
    reference_field = field()
    timestamp_field = field(default=None)

    def __attrs_post_init__(self):
        if self.timestamp_field:
            self.data.sort_values(by=[self.timestamp_field], inplace=True,ascending=False)

    def _retrieve_raw_data(self, driver, step):
        data = self.data.query(self.reference_field + " == '" + driver.journey["reference"] + "'")

        if data.shape[0]==0:
            raise StepDataNotAvailable(journey=driver.journey, step_name = step.name)

        return data.to_dict("records")[0]

    def __iter__(self):
        for idx, adm in self.data.iterrows():
            yield self._process_raw_data(adm)




