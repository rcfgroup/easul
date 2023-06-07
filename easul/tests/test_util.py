from easul.util import get_range_from_discrete_name, IntervalValue, get_text_from_range, get_current_result
import datetime as dt
import pytest

def test_get_range_from_discrete_name():
    assert get_range_from_discrete_name("age_at_admin <= -0.51", "age_at_admin") == (
    None, IntervalValue(is_equal=True, value=-0.51))
    assert get_range_from_discrete_name("s1 > 207.75", "s1") == (IntervalValue(is_equal=False, value=207.75), None)
    assert get_range_from_discrete_name("s5 <= 4.25", "s5") == (None, IntervalValue(is_equal=True, value=4.25))
    assert get_range_from_discrete_name("sex=2", "sex") == (2,)
    assert get_range_from_discrete_name("91.50 < s6 <= 98.00", "s6") == (IntervalValue(is_equal=False, value=91.5), IntervalValue(is_equal=True, value=98))
    assert get_range_from_discrete_name("UREA > 0.43", "UREA") == (IntervalValue(is_equal=False, value=0.43), None)


def test_get_text_from_range():
    assert get_text_from_range((IntervalValue(is_equal=False, value=207.75), None), lambda x: None) == "greater than 207.75"
    assert get_text_from_range((None, IntervalValue(is_equal=True, value=4.25), None), lambda x: None) == "less than 4.25"
    assert get_text_from_range((2,), lambda x: "Male" if x == 2 else "Female") == "equal Male"
    assert get_text_from_range((IntervalValue(is_equal=False, value=91.5), IntervalValue(is_equal=True, value=98)), lambda x: None) == "between 91.5 and 98"

results = [
    {"result": 0.2, "timestamp": dt.datetime(2022, 11, 21, 12, 0)},
    {"result":1, "timestamp":dt.datetime(2022,11,25,12,0)},
    {"result": 3, "timestamp": dt.datetime(2022, 11, 25, 8, 0)},
    {"result": 4, "timestamp": dt.datetime(2022, 11, 26, 8, 0)},
    {"result": 2, "timestamp": dt.datetime(2022, 11, 25, 10, 0)}
]

prov = [
    (dt.datetime(2022, 11, 25, 8, 0), results[2]),
    (dt.datetime(2022, 11, 25, 9, 59), results[2]),
    (dt.datetime(2022, 11, 20, 9, 59), None),
    (dt.datetime(2022, 11, 27, 10, 0), results[3]),
    (dt.datetime(2022, 11, 21, 12, 0, 1), results[0]),
    (dt.datetime(2022, 11, 25, 10, 0), results[4])
]

@pytest.mark.parametrize("current_ts,exp_result", prov)
def test_get_current_result(current_ts,exp_result):
    assert get_current_result(results, current_ts,"timestamp") == exp_result