import re

from easul.error import InvalidData, ValidationError, ConversionError, MissingValue

from easul.tests.example import curb65_score_algorithm
from easul.data import create_input_dataset

import pytest


TEST_API_KEY = "12345678"

curb65_data_with_invalid_values = [
    ({"confusion":"1", "urea":None,"rr":29,"sbp":"90", "dbp":"66","age":"78"}, None, None, ValidationError, re.escape("{'urea': ['null value not allowed']}")),
    ({"confusion":None, "urea":25,"rr":29,"sbp":"90", "dbp":"66","age":"78"},None, None, ValidationError, re.escape("{'confusion': ['null value not allowed']}")),
    ({"confusion":True, "urea":25,"rr":29,"sbp":"90", "dbp":"66","age":None},None, None, ValidationError, re.escape("{'age': ['null value not allowed']}")),
    ({"confusion":True, "urea":25,"rr":29,"sbp":"90", "dbp":"66","age":""},None, None, ValidationError, re.escape("{'age': ['null value not allowed']}")),
    ({"confusion": True, "urea": 25, "rr": 29, "sbp": "90", "dbp": "66"}, None, None, ConversionError, "'age' is not present"),
]
curb65_data = [
    ({"confusion":"1", "urea":"25","rr":29,"sbp":"90", "dbp":"66","age":"78"},3,"HIGH"),
    ({"confusion":0, "urea":25,"rr":29,"sbp":90, "dbp":62,"age":65},2,"MED"),
    ({"confusion":0, "urea":25,"rr":29,"sbp":90, "dbp":66,"age":64},1,"LOW"),

    ({"confusion":False, "urea":25,"rr":29,"sbp":90, "dbp":66,"age":64},1,"LOW"),
    ({"confusion":True, "urea":25,"rr":29,"sbp":90, "dbp":66,"age":64},2,"MED"),
    ({"confusion":False, "urea":17,"rr":29,"sbp":90, "dbp":66,"age":64},0,"LOW")
]


@pytest.mark.parametrize('row_data,curb65_score,rank',curb65_data)
def test_score_algorithm_with_no_errors(row_data, curb65_score, rank):
    curb65 = curb65_score_algorithm()

    dset = create_input_dataset(row_data, schema=curb65.schema)
    result = curb65.single_result(dset)
    assert result.value == curb65_score

@pytest.mark.parametrize('row_data,curb65_score,rank,error_cls,error_msg', curb65_data_with_invalid_values)
def test_score_algorithm_with_invalid_values(row_data, curb65_score, rank, error_cls, error_msg):
    curb65 = curb65_score_algorithm()

    with pytest.raises(error_cls, match=error_msg):
        dset = create_input_dataset(row_data, schema=curb65.schema)
        result = curb65.single_result(dset)
        assert result.value is None
