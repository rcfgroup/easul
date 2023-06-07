# processes are callables which receive a data structure and return a processed version of the data structure
# most of the processes defined here are classes but functions can work as well
from datetime import datetime, date, time
import logging
from typing import Callable, List, Dict, Optional

LOG = logging.getLogger(__name__)
from attrs import define, field

@define(kw_only=True)
class ExcludeFields:
    """
    Exclude specified fields from the output data
    """
    exclude_fields = field()

    def __call__(self, record):
        for exclude_field in self.exclude_fields:
            if exclude_field in record.keys():
                del record[exclude_field]

        return record

@define(kw_only=True)
class ReformatDate:
    """
    Converts field value string date in 'field_name' from a 'source_format' to a datetime object
    and then back into a string with 'target_format'
    """
    field_name:str = field()
    source_format:str = field()
    target_format:str = field()

    def __call__(self, record):
        source_date = record.get(self.field_name)

        if source_date is None:
            record[self.field_name] = None
            return

        try:
            dt = source_date if isinstance(source_date, datetime) else datetime.strptime(source_date,self.source_format)
            record[self.field_name] = dt.strftime(self.target_format)
        except ValueError:
            record[self.field_name] = None

        return record

@define(kw_only=True)
class RenameField:
    """
    Rename from_field to to_field.
    """
    from_field:str = field()
    to_field:str = field()

    def __call__(self, record):
        if self.from_field not in record:
            return record

        record[self.to_field] = record[self.from_field]
        del(record[self.from_field])
        return record

@define(kw_only=True)
class FieldApply:
    """
    Apply specified function to 'field_name' and put results in 'target_field_name'
    """
    field_name:str = field()
    target_field_name:str = field()
    fn:Callable = field()

    @target_field_name.default
    def _default_target_field_name(self):
        return self.field_name

    def __call__(self, record):
        record[self.target_field_name] = self.fn(record.get(self.field_name))
        return record

@define(kw_only=True)
class RecordApply:
    """
    Apply specified function to record (rather than specific field) and return result in the 'target_field_name'
    """
    target_field_name:str = field()
    fn:Callable = field()

    def __call__(self, record):
        record[self.target_field_name] = self.fn(record)
        return record

@define(kw_only=True)
class ConvertToFloat:
    """
    Convert values in fields to float. If not possible will return None
    """
    fields:List[str] = field()

    def __call__(self, record):
        for field in self.fields:
            try:
                record[field] = float(record[field])
            except TypeError:
                record[field] = None
            except ValueError:
                record[field] = None
            except KeyError:
                record[field] = None

        return record

@define(kw_only=True)
class ConvertToInt:
    """
    Convert values in fields to int. If not possible will return None.
    If value is a float it will be rounded to an int.
    """
    fields:List[str] = field()

    def __call__(self, record):
        for field in self.fields:
            try:
                value = float(record[field])
            except TypeError:
                value = None
            except ValueError:
                value = None

            if value is not None:
                try:
                    value = round(value)
                except ValueError:
                    value = None

            record[field] = value

        return record

@define(kw_only=True)
class MapDataItems:
    """
    Uses a dictionary of source->target 'field_map'-pings and places the result in the 'field' of the original
    record.
    """
    field_map:Dict[str,str] = field()
    field:str = field()

    def __call__(self, record):
        final_row = {}
        for src, value in record.items():
            tgt = self.field_map.get(src)
            if tgt is None:
                continue

            final_row[tgt] = value

        record[self.field] = final_row

        return record

@define(kw_only=True)
class ParseDateTime:
    """
    Parse 'field_name' string value according to 'format' into a datetime object.
    If value does not meet format it is updated with the 'default_value' which is None unless defined.
    """
    field_name:str = field()
    format:str = field()
    default_value:Optional[datetime] = field(default=None)

    def _parse_value(self, value):
        return value if isinstance(value, datetime) else datetime.strptime(value,self.format)

    def __call__(self, record):
        if self.field_name not in record:
            raise AttributeError(f"{self.__class__.__name__} '{self.field_name}' is not present in the input data")

        date_value = record.get(self.field_name)

        if date_value is None:
            record[self.field_name] = None
            return record

        try:
            dt = self._parse_value(date_value)
            record[self.field_name] = dt
        except ValueError:
            record[self.field_name] = None

        return record

@define(kw_only=True)
class ParseDate(ParseDateTime):
    """
    Parse 'field_name' string value according to 'format' and return a date object.
    If value does not meet format it is updated with None
    """
    def _parse_value(self, value):
        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        try:
            return datetime.strptime(str(value), self.format).date()
        except AttributeError:
            return self.default_value

@define(kw_only=True)
class ParseTime(ParseDateTime):
    """
    Parse 'field_name' string value according to 'format' and return a time object.
    If value does not meet format it is updated with None
    """
    def _parse_value(self, value):
        if isinstance(value, time):
            return value

        if isinstance(value, datetime):
            return value.time()

        try:
            return datetime.strptime(str(value), self.format).time()
        except AttributeError:
            return self.default_value

@define(kw_only=True)
class CombineDateTime:
    """
    Combine 'date_field' and 'time_field' to create a datetime. If any of the values are None it will use the provided
    default date/time. If
    """

    date_field:str = field()
    time_field:str = field()
    default_datetime:Optional[datetime] = field(default=None)
    output_field:str = field()

    def __call__(self, record):
        date_value = record.get(self.date_field)

        if date_value is None:
            return self.default_datetime

        time_value = record.get(self.time_field)
        if time_value is None:
            return self.default_datetime

        record[self.output_field] = datetime.combine(date_value, time_value)
        return record


@define(kw_only=True)
class FormatDateTime:
    """
    Format 'field_name' datetime object to a string based on the 'format'.
    If value is None or is not a datetime object the 'field_name' is updated to None.
    """
    field_name:str = field()
    format:str = field()

    def __call__(self, record):
        date_value = record.get(self.field_name)

        if date_value is None:
            record[self.field_name] = None
            return record

        try:
            dt = datetime.strftime(date_value, self.format)
            record[self.field_name] = dt
        except ValueError:
            record[self.field_name] = None

        return record

@define(kw_only=True)
class Age:
    """
    Calculates age in years based on date objects in 'from_field' and 'to_field'.
    Resultant age is put into 'target_field'
    """
    from_field:str = field()
    to_field:str = field()
    target_field:str = field()

    def __call__(self, record):
        record[self.target_field] = calculate_age(record.get(self.from_field), record.get(self.to_field))
        return record

@define(kw_only=True)
class MapValues:
    """
    Maps values for a particular 'field' according to a 'mappings' dictionary (option value -> mapped value).
    For example this can be used to remap character-based option keys to numbers (e.g. Male -> 0, Female -> 1,
    Other -> 2)
    """
    mappings = field()
    field = field()

    def __call__(self, record):
        record[self.field] = self.mappings.get(record[self.field])
        return record


@define(kw_only=True)
class RemoveNonNumeric:
    """
    Removes non-numeric values from 'field_name' and replaces them with 'replace_with'
    """
    field_name = field()
    replace_with=field(default=None)

    def __call__(self, record):
        try:
            float(record.get(self.field_name))
        except ValueError:
            record[self.field_name] = self.replace_with
        except TypeError:
            record[self.field_name] = self.replace_with


def calculate_age(start_date:datetime.date, end_date:datetime.date):
    if start_date is None or end_date is None:
        return None

    try:
        birthday = start_date.replace(year=end_date.year)

    # raised when birth date is February 29
    # and the current year is not a leap year
    except ValueError:
        birthday = start_date.replace(year=start_date.year,
                                      month=start_date.month + 1, day=1)
    if birthday > end_date:
        return end_date.year - start_date.year - 1
    else:
        return end_date.year - start_date.year

@define(kw_only=True)
class DefaultValues:
    """
    Replaces values in record with default 'values' if they are None.
    If 'present_flag_field' is set, it will also update this field in the record with a 1 when default values have
    been added.
    """
    values = field()
    present_flag_field = field(default=None)

    def __call__(self, record):
        if record is None and self.present_flag_field is not None:
            record = self.values
            record[self.present_flag_field] = 0
            return record

        if self.present_flag_field is not None:
            record[self.present_flag_field] = 0

        for key, value in self.values.items():
            if record.get(key):
                if self.present_flag_field is not None:
                    record[self.present_flag_field] = 1
                continue

            record[key] = value

        return record

@define(kw_only=True)
class HandleLtSign:
    """
    Handles presence of a less than prefix in the 'field_name' by reducing it by the amount specified in 'reduce_by' or
    if 'replace_value' is set, it will use this value instead.
    """
    field_name = field()
    reduce_by = field(default=None)
    replace_value = field(default=None)

    def __call__(self, record):
        value = record.get(self.field_name)

        if not value or type(value) is not str or value[0] != "<":
            return record

        if not self.reduce_by:
            record[self.field_name] = self.replace_value
        else:
            record[self.field_name] = float(value[1:]) - self.reduce_by

        return record

@define(kw_only=True)
class IfElseTest:
    """
    Returns 'true_value' or 'false_value' in 'output_field' depending on whether expression evaluates to true or false
    when supplied with the record.
    """
    expression = field()
    output_field = field()
    true_value = field()
    false_value = field()

    def __call__(self, record):
        record[self.output_field] = self.true_value if self.expression.evaluate(record) else self.false_value
        return record

@define(kw_only=True)
class SortList:
    """
    Sort input record (which must be a list) based on the 'field_name'.
    If reverse is set, sorting is in reverse.
    """
    field_name = field()
    reverse = field(default=False)

    def __call__(self, record):
        if not isinstance(record, list):
            raise AttributeError("'record' must be list")

        return sorted(record, key=lambda x: x[self.field_name], reverse=self.reverse)

@define(kw_only=True)
class GetProperty:
    """
    Gets the object in the specified 'field_name' and replaces it with the property corresponding to
    'property_name'. For example this can be used to get the 'date' from a 'datetime' object.
    """
    field_name = field()
    property_name = field()

    def __call__(self, record):
        value = record[self.field_name]
        if not value:
            record[self.field_name] = None
            return record

        prop = getattr(record[self.field_name], self.property_name)
        if callable(prop): prop = prop()

        record[self.field_name] = prop
        return record


@define(kw_only=True)
class ConvertRowsToDictionary:
    """
    Converts list input to a dictionary containing the 'fields_to_extract' from the first row of the list
    and puts the input list data into the 'output_field' of the dictionary.

    If there are no 'fields_to_extract' it will output a dictionary containing just the input list data
    in the 'output_field' of the dictionary.
    """
    output_field:str = field(default=None)
    fields_to_extract:List[str] = field(factory=list)

    def __call__(self, record):
        if type(record) is not list:
            raise AttributeError("Input data must be a list")

        if self.fields_to_extract:
            first_item = record[0] if len(record)>0 else {}
            new_record = {field:first_item.get(field) for field in self.fields_to_extract}
        else:
            new_record = {}

        new_record[self.output_field] = record

        return new_record


@define(kw_only=True)
class ExtractRowsWithExpression:
    """
    Extract rows which meet a specific field 'expression' for the 'input_field' and put them into the 'output_field'.
    The expression can be negated using 'negate_expression'
    """
    expression:"easul.expression.Expression" = field()
    input_field:str = field()
    output_field:str = field()
    negate_expression:bool = field(default=False)

    def __call__(self, record):
        input_data = record.get(self.input_field)
        if type(input_data) is not list:
            raise AttributeError(f"Input data ({self.input_field}) must be a list")

        extracted_rows = list(filter(lambda x: self.expression.evaluate(x) != self.negate_expression, record.get(self.input_field,[])))

        record[self.output_field] = extracted_rows
        return record


@define(kw_only=True)
class ExcludeRowsWithExpression:
    """
    Removes rows from list input data which meet a specific 'expression' for the supplied 'input_field'
    """
    expression = field(default=None)
    input_field = field()

    def __call__(self, record):
        if type(record) is not list:
            raise AttributeError("Input data must be a list")

        new_record = []
        for item in record:
            if self.expression.evaluate(item):
                continue
            new_record.append(item)

        return new_record


@define(kw_only=True)
class MultiRowProcess:
    """
    Process which requires input data as a list and processes each using the supplied 'processes' functions.
    """
    processes = field()

    def __call__(self, records):
        new_records = []
        for record in records:
            for process in self.processes:
                record = process(record)

            new_records.append(record)
        return new_records