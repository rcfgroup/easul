import base64
import logging
from collections import namedtuple, UserDict
from datetime import timedelta
from io import BytesIO
from itertools import chain
from uuid import uuid4

import dill
import pickle
import numpy as np

from easul.outcome import FailedOutcome
import importlib
import re

LOG = logging.getLogger(__name__)


def get_start_step(steps):
    """
    Get a start step from a set of steps. If there are multiple start steps it returns the first.
    Args:
        steps:

    Returns:

    """
    from easul.step import StartStep

    start_steps = list(filter(lambda x: isinstance(x, StartStep), steps.values()))
    if len(start_steps) == 0:
        raise SystemError("No 'StartStep' is defined in the plan")

    return start_steps[0]

def is_successful_outcome(outcome):
    """
    Determines if outcome was successful or not.
    Args:
        outcome:

    Returns:

    """
    if not outcome:
        return False

    return False if issubclass(outcome.__class__,FailedOutcome) else True

def data_to_np_array(data, fields):
    """
    Converts data to numpy array
    Args:
        data:
        fields:

    Returns:

    """
    np_data = []
    for row in data:
        np_data.append(to_np_values(row, fields))

    return np.array(np_data)


def to_np_values(field_values, fields):
    """
    Converts values to numpy values for provided fields and definitions.
    Args:
        field_values:
        fields:

    Returns:

    """
    x_values = []
    for field_name, field_details in fields.items():
        field_type = field_details['type']
        if field_type == "list":
            allowed_values = np.array(field_details.get("options"),dtype='int')
            allowed_values = allowed_values.ravel()
            num_classes = np.max(allowed_values) + 1
            x_values.append(to_categorical(field_values[field_name], num_classes))
        else:
            x_values.append([float64(field_values[field_name])])

    return list(chain.from_iterable(x_values))


def single_field_data_to_np_values(field_values, field_details):
    allowed_values = np.array(list(field_details.get("options").keys()))
    cls_to_idx = {v:idx for idx, v in enumerate(allowed_values)}
    np_values = [cls_to_idx.get(v) for v in field_values]
    num_classes = len(cls_to_idx)
    return to_categorical(np_values, num_classes)


def cast_values_using_fields(field_values, fields):
    cast_values = {}
    for field_name, field_details in fields.items():
        field_type = field_details['type']
        if field_type == "number":
            cast_values[field_name] = float64(field_values[field_name])
        else:
            cast_values[field_name] = field_values[field_name]

    return cast_values


def to_categorical(y, num_classes=None, dtype='float32'):
    y = np.array(y, dtype='int')
    input_shape = y.shape
    if input_shape and input_shape[-1] == 1 and len(input_shape) > 1:
        input_shape = tuple(input_shape[:-1])
    y = y.ravel()
    if not num_classes:
        num_classes = np.max(y) + 1
    n = y.shape[0]
    categorical = np.zeros((n, num_classes), dtype=dtype)
    categorical[np.arange(n), y] = 1
    output_shape = input_shape + (num_classes,)
    categorical = np.reshape(categorical, output_shape)

    return categorical


class Utf8EncodedImage(BytesIO):
    def decode(self):
        return base64.b64encode(self.getvalue()).decode('utf-8')


def new_id():
    return str(uuid4())

def from_serialized(serialized_data, use_pickle=False) -> "easul.algorithm.Algorithm":
    fn = pickle.loads if use_pickle else dill.loads
    return fn(serialized_data)


def to_serialized(algo, use_pickle=False):
    fn = pickle.dumps if use_pickle else dill.dumps
    return fn(algo)

def get_range_from_discrete_name(discrete_name, feature_name):
    match = re.match(f"(.*){feature_name}\s*([\<\>]*)([\=]*)\s*(-*[\d\.]+)", discrete_name)
    if not match:
        raise ValueError(f"No range could be extracted from '{discrete_name}' for feature '{feature_name}'")

    is_equal = True if match.group(3) == "=" else False


    gt = lt = False

    if match.group(2) == ">":
        gt = True

    if match.group(2) == "<":
        lt = True

    if not lt and not gt:
        return (float(match.group(4)),)

    if gt:
        return (IntervalValue(is_equal=is_equal, value = float(match.group(4))),None)

    if lt:
        lhs = None
        if match.group(1):
            match_lhs = re.match(f"(-*[\d\.]+)\s*([\<]+)([\=]*)\s*", discrete_name)
            lhs_is_equal = True if match_lhs.group(3) == "=" else False
            lhs = IntervalValue(is_equal=lhs_is_equal, value=float(match_lhs.group(1)))

        return (lhs, IntervalValue(is_equal=is_equal, value=float(match.group(4))))



def get_text_from_range(range, lookup_fn):
    if len(range)==1:
        return "equal " + str(lookup_fn(range[0]))

    if range[0] is None:
        return "less than " + str(range[1].value)

    if range[1] is None:
        return "greater than " + str(range[0].value)

    return f"between {range[0].value} and {range[1].value}"

IntervalValue = namedtuple("IntervalValue",["is_equal","value"])

def save_data(filename, data):
    serialized_data = to_serialized(data)

    with open(filename, "wb") as outfile:
        outfile.write(serialized_data)

def load_data(filename):
    with open(filename, "rb") as infile:
        algo_data = infile.read()

    return from_serialized(algo_data)

def string_to_function(value):
    if type(value) is str:
        value = create_package_class(value)

    return value() if callable(value) else value


def get_current_result(results, current_time, ts_key, sort_field=None, reverse_sort=None):
    sorted_results = sorted(results, key=lambda x:x[ts_key], reverse=True)

    results = list(filter(lambda x: x[ts_key]<=current_time, sorted_results))

    results_in_hour = list(filter(lambda x: x[ts_key]>=current_time - timedelta(hours=1), results))
    if len(results_in_hour)>0 and sort_field:
        results = sorted(results_in_hour, key=lambda x: x[sort_field], reverse=reverse_sort)

    return results[0] if len(results)>0 else None


def create_package_class(package_name):
    package_bits = package_name.split(".")
    class_name = package_bits.pop()
    module = importlib.import_module(".".join(package_bits))
    if not hasattr(module, class_name):
        raise TypeError(
            "Package module %s does not contain class %s" % (".".join(package_bits), class_name)
        )
    return getattr(module, class_name)


class NamedDict(UserDict):
    """

    """
    def __setitem__(self, key ,value):
        if hasattr(value, "name"):
            value.name = key

        super().__setitem__(key, value)


class DeferredCatalog(UserDict):
    """
    Extension of dictionary which returns a DeferredItem if
    """
    # def __getitem__(self, item):
    #     if item not in self.data:
    #         return DeferredItem(item, self)
    #
    #     return super().__getitem__(item)

    # def get(self, key):
    #     if key not in self.data:
    #         return DeferredItem(key, self)
    #
    #     return super().get(key)

    def update(self, __m, **kwargs):
        for k,v in __m.items():
            if hasattr(v, "name"):
                v.name = k

        super().update(__m)

    def __setitem__(self, key ,value):
        if hasattr(value, "name"):
            value.name = key

        super().__setitem__(key, value)


class DeferredItem:
    """
    Used to refer to an item if it has not been instantiated yet or there is a circular reference between two items (potential for
    recurrence.
    """
    def __init__(self, plan, property, name):
        self.__dict__['plan'] = plan
        self.__dict__['property'] = property
        self.__dict__['name'] = name

    def __repr__(self):
        return f"<DeferredItem name={self.name} property={self.property}>"

    def __getattr__(self, item):
        return getattr(self.plan.get_property(self.property, self.name), item)

    def __setattr__(self, key, value):
        setattr(self.plan.get_property(self.property, self.name), key, value)

    def __instancecheck__(self, instance):
        return isinstance(self.plan.get_property(self.property, self.name), instance)

    def __iter__(self):
        return iter(self.plan.get_property(self.property))

    def __eq__(self, other):
        return self.plan.get_property(self.property, self.name) == other

    def replace_plan(self, new_plan):
        self.__dict__['plan'] = new_plan


def copy_plan_with_new_sources(original_plan, new_sources):
    """
    Helper function to copy Plan and introduce new sources for simulation/testing in Jupyter notebooks.
    Args:
        original_plan:
        input_data:

    Returns:

    """
    from copy import copy
    from easul.plan import Plan

    from easul import DeferredItem
    from easul.util import DeferredCatalog

    plan_copy = Plan(
        title=original_plan.title,
        sources=DeferredCatalog(new_sources),
        schemas=copy(original_plan.schemas),
        visuals=copy(original_plan.visuals),
        algorithms=copy(original_plan.algorithms),
        steps=copy(original_plan.steps),
        states=copy(original_plan.states),
        config=copy(original_plan.config)
    )

    for name, step in plan_copy.steps.items():
        if hasattr(step, "source") and step.source:
            if isinstance(step.source, DeferredItem):
                step.source.replace_plan(plan_copy)
            else:
                step.source = new_sources.get(name)

    return plan_copy