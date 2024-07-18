import operator
from collections import UserDict
import numpy as np

from easul import error
from easul.data.checker import DataChecker
from easul.util import to_np_values, single_field_data_to_np_values, concatenate_arrays
import pandas as pd
from typing import List, Dict
from cerberus import Validator, TypeDefinition
import logging

LOG = logging.getLogger(__name__)
CATEGORY_TYPE = "category"
DF_TYPE = "df"

def validate_data_frame(df, fields):
    if len(fields) == 0:
        return

    for field_name, field_details in fields.items():
        if field_name in fields.y_names and self.x_only:
            continue

        if not field_name in df:
            raise error.ValidationError(f"Field '{field_name}' is not present in the input data")

    v = self.validator_cls(fields, allow_unknown=False)

    for idx, row in df.iterrows():
        if v.validate(row.to_dict()) is False:
            raise error.ValidationError(v.errors)


import datetime as dt


class DFType:
    included_types = ["df"]

    def __eq__(self, other):
        return isinstance(other, pd.DataFrame)


class DataValidator(Validator):
    """
    Cerberus Validator for DataSet schema. Includes additional type mapping for 'time' and additional validation
    parameters: 'help', 'options', 'output', 'label' and 'pre_convert'
    """

    types_mapping = Validator.types_mapping.copy()
    types_mapping[CATEGORY_TYPE] = TypeDefinition(CATEGORY_TYPE, (object,), ())
    types_mapping[DF_TYPE] = TypeDefinition(DF_TYPE, (pd.DataFrame,), ())
    types_mapping["time"] = TypeDefinition('time', (dt.time,), ())

    def _validate_help(self, constraint, field, value):
        """{'type': 'string'}"""
        pass

    def _validate_options(self, constraint, field, value):
        """{'type': 'dict'}"""
        if value not in constraint:
            self._error(field, f"Value '" + str(value) + "' is not defined in options")

    def _validate_output(self, constraint, field, value):
        """{'type': 'string'}"""
        pass

    def _validate_label(self, constraint, field, value):
        """{'type': 'string'}"""
        pass

    def _validate_pre_convert(self, constraint, field, value):
        """{'type': 'string'}"""
        pass

    def _validate_type(self, schema, field, value):
        super()._validate_type(schema, field, value)

        validate_data_frame(value, self.schema[field])
        # if isinstance(value, Sequence) and not isinstance(value, _str_type):
        #     self.__validate_schema_sequence(field, schema, value)
        # elif isinstance(value, Mapping):
        #     self.__validate_schema_mapping(field, schema, value)


class DataSchema(UserDict):
    """
    Schema used by algorithms to define format of input data.
    Field definitions utilise 'cerberus' library to validate input data.
    """

    def __init__(self, schema: Dict[str, Dict], y_names=None):

        if not y_names:
            y_names = []

        self.y_names: List[str] = y_names

        if not all([name in schema for name in y_names]):
            raise AttributeError(f"Not all y_names {y_names} are in schema definition {list(schema.keys())}")

        super().__init__(schema)

        self.refresh()

    def refresh(self):
        if self.filter({"type": "category", "output": "onehot"}, include_x=False, include_y=True):
            self.single_y = False
        else:
            self.single_y = True if len(self.y_names) == 1 else False

        category_fields = self.filter({"type": "category"}, include_x=True, include_y=True)

        for category_field_name, category_details in category_fields.items():
            if not category_details.get("options"):
                raise error.ValidationError(
                    f"Field '{category_field_name}' with 'category' type must have 'options' provided")

    @property
    def x(self):
        return {name: self.data[name] for name in filter(lambda x: x in self.x_names, self.data.keys())}

    @property
    def y(self):
        return {name: self.data[name] for name in filter(lambda x: x in self.y_names, self.data.keys())}

    def to_x_values(self, field_values):
        return to_np_values(field_values, self.x)

    def to_y_values(self, field_values):
        return to_np_values(field_values, self.y)

    @property
    def help(self):
        help_lines = [self._help_line(k, v) for k, v in self.data.items()]
        help_lines.extend(["* = required field", "** = target y value"])

        return help_lines

    def _help_line(self, name, info):
        return f"- {name}: {info.get('help')}" + ("*" if info.get("required") else " ") + "(" + info.get("type",
                                                                                                         "any") + ")" + (
            "**" if name in self.y_names else "")

    def filter(self, criteria=None, include_x=True, include_y=False):
        filtered = {}

        for name, info in self.items():
            include = True

            if include_x and include_y and name not in self.data:
                continue
            elif include_x and not include_y and name not in self.x_names:
                continue
            elif include_y and not include_x and name not in self.y_names:
                continue

            if criteria:
                for filt_k, filt_v in criteria.items():
                    if filt_k in info and info[filt_k] != filt_v:
                        include = False

            if include is True:
                filtered[name] = info

        return filtered

    def filter_names(self, **kwargs):
        filtered = self.filter(**kwargs)
        return list(filtered.keys())

    @property
    def x_names(self):
        return list(filter(lambda x: x not in self.y_names, self.data.keys()))

    @property
    def unique_digest(self):
        return "X"

    def is_categorical(self, name):
        if self.get(name, {}).get("type") in ["category", "list"]:
            return True

        return False


def np_random_splitter(data, train_size, **kwargs):
    """Numpy-based random splitter through permutation
    """
    train_no = round(data.shape[0] * train_size)
    test_no = data.shape[0] - train_no
    rnd_indexes = list(np.random.permutation(data.index))
    train_idx = rnd_indexes[slice(0, train_no)]
    test_idx = rnd_indexes[slice(train_no, test_no + train_no)]

    train = data.loc[train_idx, :]
    test = data.loc[test_idx, :]

    return train, test


class DataInput:
    """
    Data and schema combined including automatic data conversion and access to data in particular forms.
    Support for pandas DataFrames and list of dictionaries (which are internally converted).
    """
    validator_cls = DataValidator
    checker_cls = DataChecker

    def __init__(self, data, schema: DataSchema, convert: bool = True, validate: bool = True, encoded_with=None,
                 encoder=None, x_only=False, checker_cls=None):
        if encoded_with is not None and encoded_with != encoder:
            raise AttributeError("Data input encoded with different encoder than the defined one")
        checker_cls = DataInput.checker_cls if not checker else checker
        self.x_only = x_only
        self.schema = schema
        self.checker = checker_cls(self.schema.filter(include_x=True, include_y=not self.x_only))
        self._convert = convert
        self._validate = validate
        self.encoded_with = encoded_with
        self.encoder = encoder
        self._data = None
        self.data = data

    @property
    def is_encoded(self):
        return self.encoded_with is not None

    def is_matching_encoder(self, encoder):
        return self.encoded_with == encoder

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._init_data(value)

    def _init_data(self, data):
        try:
            if self._convert:
                data = self.checker.convert_data(data)
        except BaseException as ex:
            raise error.ConversionError(message="Unable to convert data", orig_exception=ex, data=data)

        data = self.clean(data)
        LOG.info(f"data:{data}")
        if self._validate:
            self.checker.validate(data)

        self._data = self._process_data(data)

    # def convert_data(self, data):
    #     data = self.checker._convert_data(data, self.schema.filter(include_x=True, include_y=not self.x_only))
    #     LOG.info(f"convert_data:{data}")
    #     return data

    # def validate(self, data):
    #     if type(data) is list:
    #         [self._validate_data(item, self.schema) for item in data]
    #     else:
    #         self._validate_data(data, self.schema)

    def clean(self, data):
        return data

    # def _convert_data(self, data, fields, convertors = None):
    #     return self.checker._convert_data(data)

    def _process_data(self, data):
        if type(data) is dict:
            return pd.DataFrame(data=[data])
        if type(data) is list:
            return pd.DataFrame(data=data)

        return data

    # def _validate_data(self, data, fields):
    #     if len(fields)==0:
    #         return
    #
    #     for field_name, field_details in fields.items():
    #         if not field_name in data:
    #             raise error.ValidationError(f"Field '{field_name}' is not present in the input data")
    #
    #     v = self.validator_cls(fields, allow_unknown=False)
    #
    #     # if type(data) is list:
    #     #     for row in data:
    #     #         if v.validate(row) is False:
    #     #             raise error.ValidationError(v.errors)
    #     # else:
    #     LOG.info(f"data:{data}")
    #     if v.validate(data) is False:
    #         raise error.ValidationError(v.errors)

    @property
    def Y_array(self):
        """

        Returns: Y values in the form of an array of np.arrays

        """
        return self.data[self.schema.y_names].to_numpy()

    @property
    def Y(self):
        """

        Returns: Y values from the Y array (e.g. the first value) as an np.array

        """
        data = self._extract_data(self.schema.y_names)

        if self.schema.single_y:
            return [item[0] for item in data]

        return data

    @property
    def X(self):
        LOG.info(f"x_names:{self.schema.x_names}")
        return self._extract_data(self.schema.x_names)

    def _extract_data(self, field_names):
        data = self.data[field_names]

        if not self.encoder:
            return data.to_numpy()

        idx = 0
        output = None
        return self.encoder(field_names, data.to_numpy(), self.schema)

    @property
    def X_data(self):
        """

        Returns: A pandas DataFrame containing just X values.

        """

        if len(self.schema.x_names) == 0:
            return []

        return self.data[self.schema.x_names]

    @property
    def Y_data(self):
        """

        Returns: A pandas DataFrame containing just Y values

        """

        if len(self.schema.y_names) == 0:
            return []

        return self.data.loc[:, self.schema.y_names]

    def train_test_split(self, train_size=None, test_size=None, splitter=np_random_splitter, **kwargs):
        if not train_size and not test_size:
            raise AttributeError("train_size or test_size must be provided")

        if not train_size:
            train_size = 1 - test_size

        train, test = splitter(self.data, train_size, **kwargs)

        data_cls = self.__class__
        if isinstance(self.data, pd.DataFrame):
            data_cls = DFDataInput

        train_ds = data_cls(data=train, schema=self.schema, convert=False, validate=False)

        test_ds = data_cls(data=test, schema=self.schema, convert=False, validate=False)

        return train_ds, test_ds

    def __repr__(self):
        data = self.data.to_dict("records") if isinstance(self.data, pd.DataFrame) else self.data
        return f"<{self.__class__.__name__} data={data}, schema={self.schema}>"

    def asdict(self):
        return self.data.to_dict("records") if isinstance(self.data, pd.DataFrame) else self.data

    def clean(self, data):
        new_data = []

        for idx, row in enumerate(data):
            new_row = {}
            for column, value in row.items():
                if column in self.schema:
                    new_row[column] = value

            new_data.append(new_row)

        return new_data


class DFDataInput(DataInput):
    """
    Data input underpinned by pandas DataFrame inputs.
    """
    convertors = {
        "number": lambda x, y: x.astype("float"),
        "float": lambda x, y: DFDataInput.to_float(x),
        "date": lambda x, y: pd.to_datetime(x, format=y["format"]),
        "datetime": lambda x, y: pd.to_datetime(x),
        "category": lambda x, y: x.astype("category"),
        "integer": lambda x, y: x.astype("int64"),
        "list": lambda x, y: list(x),
        "string": lambda x, y: x.astype("string"),
        "boolean": lambda x, y: DFDataInput.to_boolean(x)
    }

    @classmethod
    def to_boolean(cls, value):
        if type(value[0]) is str:
            if value[0] == "":
                return [None]

            value = value.astype("int64")

        return value.astype("boolean")

    @classmethod
    def to_float(cls, value):
        if type(value[0]) and value[0] == "" or value[0] is None:
            return pd.Series(np.nan() * len(value))

        return value.astype("float")

    def _validate_data(self, data, fields):
        if len(fields) == 0:
            return

        for field_name, field_details in fields.items():
            if field_name in fields.y_names and self.x_only:
                continue

            if not field_name in data:
                raise error.ValidationError(f"Field '{field_name}' is not present in the input data")

        v = self.validator_cls(fields, allow_unknown=False)

        for idx, row in data.iterrows():
            if v.validate(row.to_dict()) is False:
                raise error.ValidationError(v.errors)

    def clean(self, data):
        for column in data.columns:
            if column in self.schema:
                continue

            del data[column]

        return data

    def _process_data(self, data):
        return data


class SingleDataInput(DataInput):
    """
    Data input containing a single row of inputs (e.g. dictionary or DataFrame) which follow the schema.
    This is used to handle single element predictions/interpretations from user supplied values.
    """

    def convert_data(self, data):
        if not self._convert:
            return data

        data = self._convert_data(data, self.schema.x)

        return data

    def validate(self, data):
        self._validate_data(data, self.schema.x)

    @property
    def Y(self):
        raise ValueError("Y values are not available in SingleInputDataSet")

    @property
    def Y_scalar(self):
        raise ValueError("Y scalar values are not available in SingleInputDataSet")

    @property
    def X_data(self):
        return self.data

    @property
    def Y_data(self):
        raise ValueError("Y data is not available in SingleInputDataSet")

    def __getitem__(self, item):
        return self._data[item][0]

    def get(self, item, default=None):
        try:
            return self[item]
        except ValueError:
            return default

    def asdict(self):
        return self.data.to_dict("records")[0]

    def clean(self, data):
        new_data = {}
        for column, value in data.items():
            if column not in self.schema:
                continue

            new_data[column] = value

        return new_data


class MultiDataInput(DataInput):
    """
    Data input containing multiple rows (e.g. list or DataFrame) which follow the schema.
    This is used to handle multiple element predictions/interpretations from user supplied values.
    """

    def _init_data(self, data):
        if isinstance(data, list):
            data = pd.DataFrame(data=data, index=[0])

        self._data = self._convert_data(data, self.schema.x)

    @property
    def Y(self):
        raise ValueError("Y values are not available in MultiInputDataSet")

    @property
    def Y_scalar(self):
        raise ValueError("Y scalar values are not available in MultiInputDataSet")

    @property
    def X_data(self):
        return self.data

    @property
    def Y_data(self):
        raise ValueError("Y data is not available in MultiInputDataSet")


def check_and_encode_data(data, encoder):
    """
    Check and encode data if it has not already been encoded. If data has already been encoded but is different
    throws a SystemError.
    Args:
        data:
        encoder:

    Returns:

    """
    if data.encoded_with is None and encoder is None:
        return data

    if data.is_encoded:
        if data.is_matching_encoder(encoder) is False:
            raise SystemError(
                f"Data was not encoded in the same way as the supplied encoder (data set encoded_with:{data.encoded_with}, supplied encoder:{encoder})")
        else:
            return data

    return data


def create_input_dataset(data, schema=None, allow_multiple=False, encoder=None):
    """
    Create input dataset according to input data. If it already a DataInput class. And if a dictionary then returns a
    SingleDataInput, or if a list it returns a MultiDataInput. If no schema is provided raises and exception.

    Args:
        data:
        schema:
        allow_multiple:
        encoder:

    Returns:

    """
    from easul import data as dat

    # if allow_multiple is False and (isinstance(data, dat.MultiDataInput) or isinstance(data, list)):
    #     raise AttributeError("data must represent a single row (e.g. a SingleInputDataSet or a dictionary)")

    if issubclass(data.__class__, DataInput):
        return check_and_encode_data(data, encoder)

    if not schema:
        raise AttributeError("schema is required if data is not already a DataSet")

    elif type(data) is list:
        return check_and_encode_data(dat.MultiDataInput(data, schema, convert=True, encoder=encoder), encoder)

    return check_and_encode_data(dat.SingleDataInput(data, schema, convert=True, encoder=encoder), encoder)


class InputEncoder:
    """
    Base encoder which encodes input data according to supplied encoding functions for each field.
    """

    def __init__(self, encodings):
        self.encodings = encodings

    # def encode_input(self, dinput):
    #     for field_name,encoder_fn in self.encodings.items():
    #         dinput.data[field_name] = self.encode_field(field_name, dinput.data, dinput.schema)

    def encode_field(self, field_name, data, schema):
        encoder_fn = self.encodings.get(field_name)
        if not encoder_fn:
            return data[field_name]

        return encoder_fn(field_name, data[field_name], schema[field_name])

    def is_field_encoded(self, field_name):
        return field_name in self.encodings


def get_field_options_from_schema(field_name, schema):
    """
    Extract field options from the DataSchema as a dictionary.
    Args:
        field_name:
        schema:

    Returns:

    """
    options = schema[field_name]["options"]
    return dict(sorted(options.items(), key=operator.itemgetter(0)))


def one_hot_encoding(field_name, data, schema):
    return single_field_data_to_np_values(data, schema)