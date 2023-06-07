from easul import process

def test_HandleLtSign_returns_reduced_value():
    lt_sign = process.HandleLtSign(field_name="value",reduce_by=0.1)
    assert lt_sign({"value":"<0.5"}) == {"value":0.4}

def test_HandleLtSign_returns_replaced_value():
    lt_sign = process.HandleLtSign(field_name="value",replace_value=None)
    assert lt_sign({"value":"<0.5"}) == {"value":None}

def test_DefaultValues_replace_null_value_for_specified_fields():
    dv = process.DefaultValues(values={"sbp":160, "dbp":90})
    assert dv({"sbp":None,"dbp":80}) == {"sbp":160,"dbp":80}
    assert dv({"sbp": "", "dbp": 80}) == {"sbp": 160, "dbp": 80}
    assert dv({"sbp": False, "dbp": 80}) == {"sbp": 160, "dbp": 80}
    assert dv({"sbp": 0, "dbp": 80}) == {"sbp": 160, "dbp": 80}

import datetime as dt
def test_ParseDateTime_replaces_string_with_datetime():
    pdt = process.ParseDateTime(field_name="timestamp",format="%Y-%m-%d %H:%M")
    assert pdt({"timestamp":"2018-03-02 12:23"}) == {"timestamp":dt.datetime(2018,3,2,12,23)}
    assert pdt({"timestamp": None}) == {"timestamp": None}
    assert pdt({"timestamp": "03/04/2018"}) == {"timestamp": None}
