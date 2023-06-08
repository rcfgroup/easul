import os
from typing import Any

from easul import util
from easul.algorithm.result import Result
from abc import abstractmethod
import dill
import hashlib
from attrs import define, field
from easul.data import create_input_dataset, DataInput
import logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


@define(kw_only=True)
class Algorithm:
    """
    Base class for algorithms
    """
    title:str = field()
    schema:Any = field()
    encoder = field(default=None)

    def __post_init__(self):
        self.id = str(util.new_id())

    def to_serialized(self):
        return util.to_serialized(self)

    @abstractmethod
    def serialize_with_dataset_id(self):
        pass

    @property
    def unique_digest(self)->str:
        """
        Generate unique digest for algorithm
        Returns: hex digest

        """
        algo_dump = dill.dumps(self)
        return hashlib.sha256(algo_dump).hexdigest()

    @abstractmethod
    def single_result(self, data:Any)->Result:
        """
        Execute algorithm based on input data
        Args:
            data: input data

        Returns: an algorithm result object

        """
        pass

    def create_input_dataset(self, data:Any)->DataInput:
        return create_input_dataset(data=data, schema=self.schema, encoder=self.encoder)

    def save(self, filename:str):
        """
        Save algorithm
        Args:
            filename:

        """
        from easul.util import save_data
        save_data(filename, self)

    def describe(self):
        """
        Describes the algorithm

        Returns: dictionary containing key elements

        """
        return {
            "title":self.title,
            "type":self.__class__.__name__
        }

@define(kw_only=True)
class StoredAlgorithm(Algorithm):
    """
    Stored algorithm which updates from a file through load_algorithm or a source definition.
    Acts as a decorator for the underlying algorithm.
    """
    filename:str = field()
    definition: str = field()
    _algorithm = field(init=False)
    schema = field(init=False)
    encoder = field(init=False)

    def __attrs_post_init__(self):
        filename = self.filename
        if os.path.exists(filename):
            self.update_from_file(filename)
        else:
            LOG.warning(f"Algorithm file '{filename}' does not exist")
            self.update_from_definition()

    def update_from_definition(self):
        from easul.util import create_package_class
        if callable(self.definition):
            algorithm_def = self.definition
        else:
            algorithm_def = create_package_class(self.definition)
        algorithm = algorithm_def() if callable(algorithm_def) else algorithm_def
        self._algorithm = algorithm
        self.schema = algorithm.schema

    def update_from_file(self, filename):
        algorithm = util.load_data(filename)
        self._algorithm = algorithm
        self.schema = algorithm.schema

    def __getattr__(self, item):
        return getattr(self._algorithm, item)

    def single_result(self, data):
        return self._algorithm.single_result(data)

    @property
    def unique_digest(self):
        return self._algorithm.unique_digest

    def save_to_file(self, filename=None):
        from easul.util import save_data
        if not filename:
            filename = self.filename
        save_data(filename, self._algorithm)

    def describe(self):
        return {
            "title":self._algorithm.title,
            "type":self._algorithm.__class__.__name__ + " (StoredAlgorithm)",
            "filename":self.filename
        }



