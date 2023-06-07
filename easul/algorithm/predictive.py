from abc import abstractmethod
from typing import Any, Optional

import numpy as np

import easul.data as ds
import easul.util
from easul.algorithm.result import ClassifierResult, RegressionResult, Probability

from .algorithm import Algorithm
import hashlib

from enum import auto, Enum
from easul.data import get_field_options_from_schema
import logging
from attrs import define, field
LOG = logging.getLogger(__name__)

class PredictiveTypes(Enum):
    REGRESSION = auto()
    CLASSIFICATION = auto()

@define(kw_only=True, eq=False)
class PredictiveAlgorithm(Algorithm):
    """
    Base predictive algorithm based on AI or ML model. Includes support for an encoder and schema which are applied
    on the input data if required.

    """
    result_class = None
    model:Any = field()
    schema:ds.DataSchema = field()
    encoder:Optional[ds.InputEncoder] = field(default=None)
    unique_id = field(init=False)

    @unique_id.default
    def _default_unique_id(self):
        return str(easul.util.new_id())

    def fit(self, dataset):
        dataset = ds.create_input_dataset(data=dataset, schema=self.schema, encoder=self.encoder, allow_multiple=True)
        self.model.fit(dataset.X, dataset.Y)

    def serialize_with_dataset_id(self):
        return easul.util.to_serialized(self)

    @property
    def unique_digest(self):
        digest = str(self.schema.unique_digest + "_" + self.unique_id).encode("utf-8")

        return hashlib.sha256(digest).hexdigest()

    @property
    def help(self):
        model_cls = self.model.__class__

        return {
            "type":model_cls.__name__
        }

    @abstractmethod
    def _create_result(self, prediction):
        pass


    def __eq__(self, other):
        return self.unique_digest == other.unique_digest



@define(kw_only=True)
class RegressionAlgorithm(PredictiveAlgorithm):
    """
    Regression-specific version of the PredictiveAlgorithm which returns a result with a continuous value.
    """
    result_class = RegressionResult

    def single_result(self, data):
        dset = ds.create_input_dataset(data, self.schema, allow_multiple=False, encoder=self.encoder)
        pns = self.model.predict(dset.X)

        return RegressionResult(value=pns[0], data=dset)


@define(kw_only=True, eq=False)
class ClassifierAlgorithm(PredictiveAlgorithm):
    """
    Classifier-specific version of the PredictiveAlgorithm which returns a result containing a value, label
    and a list of probabilities for each potential class.
    """
    def single_result(self, data, round_dp=2):
        dset = ds.create_input_dataset(data, self.schema, allow_multiple=False, encoder=self.encoder)
        pns = self.model.predict(dset.X)
        prob_rows = self.model.predict_proba(dset.X)
        field_name = self.schema.y_names[0]
        option_list = get_field_options_from_schema(field_name, self.schema)

        if round_dp:
            prob_rows = np.round_(prob_rows, round_dp)

        probs = [Probability(*args) for args in zip(prob_rows[0], option_list.values(), option_list.keys())]

        return ClassifierResult(value=pns[0], label=option_list.get(pns[0]), probabilities=probs, data=dset)
