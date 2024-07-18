import pandas as pd
import numpy as np
import datetime as dt

class DataChecker:
    convertors = {
        "number": DataChecker.to_float,
        "float": DataChecker.to_float,
        "date": lambda x, y: dt.datetime.strptime(x, y["format"]) if isinstance(x, str) else x,
        "datetime": lambda x, y: DataChecker.to_datetime(x, y) if isinstance(x, str) else x,
        "time": lambda x, y: DataChecker.to_datetime(x, y).time() if isinstance(x, str) else x,
        "category": lambda x, y: x,
        "integer": lambda x, y: np.int64(x),
        "list": lambda x, y: list(x) if x else [],
        "string": lambda x, y: str(x),
        "boolean": DataChecker.to_boolean
    }

    @classmethod
    def to_datetime(cls, value, config):
        if type(value) is dt.datetime:
            return value

        return dt.datetime.strptime(value, config.get("format", "%Y-%m-%dT%H:%M:%S"))

    @classmethod
    def to_boolean(value, details):
        """
        Tries to convert a numeric value or string (e.g. 0 or 1) to a boolean

        Args:
            value: Input value
            details:

        Returns:

        """
        if value is None:
            return None

        if type(value) is str:
            if value == "":
                return None

            value = np.int64(value)

        return bool(value)

    @classmethod
    def to_float(value, details):
        """
        Tries to convert a value to a float

        Args:
            value: Input value
            details:

        Returns:

        """
        if value is None:
            return None

        if value == "":
            return None

        if type(value) is bool:
            value = bool(value)

        return float(value)

    def __init__(self, fields):
        self.fields = fields

    def validate_data(self, data):
        if len(fields)==0:
            return

        for field_name, field_details in self.fields.items():
            if not field_name in data:
                raise error.ValidationError(f"Field '{field_name}' is not present in the input data")

        v = self.validator_cls(self.fields, allow_unknown=False)

        LOG.info(f"data:{data}")
        if v.validate(data) is False:
            raise error.ValidationError(v.errors)

    def convert_data(self, data, fields):
        for field_name, field_details in fields.items():
            try:
                if field_name not in data:
                    if "required" in field_details:
                        raise error.ValidationError(f"Field '{field_name}' is not present in the input data")
                    else:
                        continue

                prev_convert = field_details.get("pre_convert")
                if prev_convert:
                    pre_convert_fn = self.convertors.get(prev_convert)
                    data[field_name] = pre_convert_fn(data[field_name], field_details)

                field_type = field_details['type']
                if field_details.get("schema"):
                    data[field_name] = self._convert_data(data[field_name], field_details["schema"])
                    continue

                convert_fn = self.convertors.get(field_type)
                if not convert_fn:
                    raise error.ConversionError(
                        f"Field conversion function not available to convert '{field_name}' to type '{field_type}'",
                        orig_exception=Exception, data=data)

                data[field_name] = convert_fn(data[field_name], field_details)
            except Exception as ex:
                raise error.ConversionError(f"Unexpected error converting '{field_name}'", orig_exception=ex)

        return data


class DFDataChecker(DataChecker):
    convertors = {
        "number": lambda x, y: x.astype("float"),
        "float": lambda x, y: DFDataChecker.to_float(x),
        "date": lambda x, y: pd.to_datetime(x, format=y["format"]),
        "datetime": lambda x, y: pd.to_datetime(x),
        "category": lambda x, y: x.astype("category"),
        "integer": lambda x, y: x.astype("int64"),
        "list": lambda x, y: list(x),
        "string": lambda x, y: x.astype("string"),
        "boolean": lambda x, y: DFDataChecker.to_boolean(x)
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

    def validate_data(self, data):
        v = self.validator_cls(fields, allow_unknown=False)

        for idx, row in data.iterrows():
            if v.validate(row.to_dict()) is False:
                raise error.ValidationError(v.errors)