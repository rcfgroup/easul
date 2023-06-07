import numpy as np

from easul import error
import pytest
from easul import data
from easul.data import one_hot_encoding
import logging
LOG = logging.getLogger(__name__)


def test_schema_returns_x_and_y_fields():
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": {"type": "list", "allowed": [1, 2]},
            "BMI": {"type": "number"},
            "BP": {"type": "number"},
            "S1": {"type": "number"},
            "S2": {"type": "number"},
            "S3": {"type": "number"},
            "S4": {"type": "number"},
            "S5": {"type": "number"},
            "S6": {"type": "number"},
            "Y": {"type": "number"}
        }, y_names=["Y"]
    )
    assert list(schema.x.keys()) == ["AGE","SEX","BMI","BP","S1","S2","S3","S4","S5","S6"]
    assert list(schema.y.keys()) == ["Y"]

def test_schema_fails_if_y_names_not_in_schema():
    with pytest.raises(AttributeError):
        data.DataSchema(
            schema={
                "AGE": {"type": "number"},
                "SEX": {"type": "list", "allowed": [1, 2]},
                "BMI": {"type": "number"},
                "BP": {"type": "number"},
                "S1": {"type": "number"},
                "S2": {"type": "number"},
                "S3": {"type": "number"},
                "S4": {"type": "number"},
                "S5": {"type": "number"},
                "S6": {"type": "number"},
                "Y": {"type": "number"}
            }, y_names=["score"]
        )

def test_dataset_x_and_y_output_as_np_arrays(regression_dataset):
    assert np.array_equal(regression_dataset.X[0], np.array([59., 2  , 32.1  , 101.   , 157. , 93.2,
                                                             38.  , 4.  , 4.8598 , 87.]))
    assert regression_dataset.Y[0] == 151.0


def test_dataset_fails_if_invalid_option():
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": {"type": "category", "options": {1: "Male", 2: "Female"}, "pre_convert":"integer"},
            "Y": {"type": "number"}
        }, y_names=["Y"]
    )

    with pytest.raises(error.ValidationError, match="SEX.+Value '3' is not defined in options"):
        data.DataInput(data=[
            {"AGE": 59, "SEX": 2, "BMI": 32.1, "Y":32},
            {"AGE": 63, "SEX": 3, "BMI": 29.1,
             "Y": 98}], schema=schema)

def test_dataschema_fails_if_no_options_for_category():
    with pytest.raises(error.ValidationError, match="Field 'SEX' with 'category' type must have 'options' provided"):
        schema = data.DataSchema(
            schema={
                "AGE": {"type": "number"},
                "SEX": {"type": "category"},
                "Y": {"type": "number"}
            }, y_names=["Y"]
        )



def test_dataset_returns_x_and_y_values_as_np_arrays_with_value_encoding():
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": {"type": "category", "options": {1:"Male",2:"Female"}},
            "BMI": {"type": "number"},
            "BP": {"type": "number"},
            "S1": {"type": "number"},
            "S2": {"type": "number"},
            "S3": {"type": "number"},
            "S4": {"type": "number"},
            "S5": {"type": "number"},
            "S6": {"type": "number"},
            "Y": {"type": "number"}
        }, y_names=["Y"]
    )

    dset = data.DataInput(data=[{"AGE":59, "SEX":2, "BMI":32.1, "BP":101, "S1":157, "S2":93.2, "S3":38, "S4":4, "S5":4.9, "S6":87, "Y":142}, {"AGE":63, "SEX":1, "BMI":29.1, "BP":114, "S1":121, "S2":80.4, "S3":37, "S4":2, "S5":2.7, "S6":65, "Y":98}], schema=schema)

    assert np.array_equal(dset.X, [[ 59. ,   2 ,  32.1, 101. , 157. ,  93.2,  38. , 4. ,   4.9,  87. ],
                      [ 63. ,   1. ,  29.1, 114. , 121. ,  80.4,  37. , 2. ,   2.7,  65. ]
                      ])

    assert np.array_equal(dset.Y, [142.,98.])

def test_dataset_returns_x_values_as_np_arrays_with_one_hot_encoding():
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": {"type": "category", "options": {1:"Male",2:"Female"}},
            "BMI": {"type": "number"},
            "BP": {"type": "number"},
            "Y": {"type": "number"}
        }, y_names=["Y"]
    )
    encoder = data.InputEncoder(encodings={"SEX":one_hot_encoding})
    dset = data.DataInput(data=[{"AGE":59, "SEX":2, "BMI":32.1, "BP":101, "Y":142}, {"AGE":63, "SEX":1, "BMI":29.1, "BP":114, "Y":98}], schema=schema, encoder=encoder)

    assert np.array_equal(dset.X, np.array([[ 59. ,   0,1 ,  32.1, 101. ],
                      [ 63. ,   1,0 ,  29.1, 114. ]
                      ]))

    assert np.array_equal(dset.Y, np.array([142.,98.]))


def test_dataset_returns_y_values_as_np_arrays_with_one_hot_encoding():
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": {"type": "category", "options": {"1":"Male","2":"Female"}},
            "BMI": {"type": "number"},
            "BP": {"type": "number"},
            "Y": {"type": "category", "options": {"0":"False","1":"True"}}
        }, y_names=["Y"]
    )
    encoder = data.InputEncoder(
        encodings={
            "SEX": one_hot_encoding,
            "Y": one_hot_encoding
        }
    )
    dset = data.DataInput(data=[{"AGE": 59, "SEX": "2", "BMI": 32.1, "BP": 101, "Y": "0"},
                                {"AGE": 63, "SEX": "1", "BMI": 29.1, "BP": 114, "Y": "1"},
                                {"AGE": 42, "SEX": "1", "BMI": 30.1, "BP": 134, "Y": "0"}
                                ], schema=schema, encoder=encoder)

    assert np.array_equal(dset.Y, np.array([[1,0],[0,1],[1,0]]))

def test_schema_filter_based_on_criteria():
    sex_details = {"type": "category", "options": {1:"Male", 2:"Female"}}
    y_details = {"type": "category", "options":{0:"No",1:"Yes"}}
    schema = data.DataSchema(
        schema={
            "AGE": {"type": "number"},
            "SEX": sex_details,
            "BMI": {"type": "number"},
            "BP": {"type": "number"},
            "S1": {"type": "number"},
            "S2": {"type": "number"},
            "S3": {"type": "number"},
            "S4": {"type": "number"},
            "S5": {"type": "number"},
            "S6": {"type": "number"},
            "Y": y_details
        }, y_names=["Y"]
    )
    assert schema.filter_names(criteria={"type":"category"}) == ["SEX"]
    assert schema.filter(criteria={"type": "category"}) == {"SEX":sex_details}
    assert schema.filter(criteria={"type": "category"}, include_x=False, include_y=True) == {"Y": y_details}
    assert schema.filter(criteria={"type": "category"}, include_x=True, include_y=False) == {"SEX": sex_details}
    assert schema.filter(criteria=sex_details, include_x=True, include_y=False) == {"SEX": sex_details}
    assert schema.filter(criteria={"type":"number"}, include_x=True, include_y=False) == {
        "AGE": {"type": "number"},
        "BMI": {"type": "number"},
        "BP": {"type": "number"},
        "S1": {"type": "number"},
        "S2": {"type": "number"},
        "S3": {"type": "number"},
        "S4": {"type": "number"},
        "S5": {"type": "number"},
        "S6": {"type": "number"}
    }
    assert schema.filter(criteria={"type": "category"}, include_x=True, include_y=True) == {"SEX": sex_details,"Y": y_details}


def test_train_test_split_works(mock_ids):
    from easul.tests.example import load_diabetes
    diabetes = load_diabetes(raw=True)
    assert diabetes.data.shape == (442, 11)
    train, test = diabetes.train_test_split(0.8)
    assert train.data.shape == (354, 11)
    assert test.data.shape == (88, 11)


def test_single_value_data_set_returns_processed_values_with_converted_category():
    schema = data.DataSchema(
        schema={
            "age": {"type": "number"},
            "sex": {"type": "category", "options": {1:"Male", 2:"Female"}, "pre_convert":"number"},
            "bmi": {"type": "number"},
            "bp": {"type": "number"},
            "s1": {"type": "number"},
            "s2": {"type": "number"},
            "s3": {"type": "number"},
            "s4": {"type": "number"},
            "s5": {"type": "number"},
            "s6": {"type": "number"},
            "y": {"type": "category",  "options":{0:"No",1:"Yes"}}
        }, y_names=["y"]
    )

    input_data = {"diabetes_id": "1", "age": "59.0", "sex": "2", "bmi": "32.1", "bp": "101.0", "s1": '157.0', "s2": '93.2', "s3": '38.0', "s4": '4.0', "s5": '4.8598', "s6": '87.0'}

    ds = data.SingleDataInput(data=input_data, schema=schema, convert=True)
    assert np.array_equal(ds.X[0], [59.0,2,32.1,101.0,157.0,93.2,38.0,4.0,4.8598,87.0])

def test_data_set_returns_data_according_to_schema():
    schema = data.DataSchema(
        schema={
            "age": {"type": "number"},
            "sex": {"type": "category", "options": {1:"Male",2:"Female"}, "pre_convert":"number"},
            "bmi": {"type": "number"},
            "bp": {"type": "number"},
            "s1": {"type": "number"},
            "s2": {"type": "number"},
            "s3": {"type": "number"},
            "s4": {"type": "number"},
            "s5": {"type": "number"},
            "s6": {"type": "number"},
            "y": {"type": "number"}
        }, y_names=["y"]
    )

    input_data = [{"diabetes_id": "1", "age": "59.0", "sex": "2", "bmi": "32.1", "bp": "101.0", "s1": '157.0', "s2": '93.2', "s3": '38.0', "s4": '4.0', "s5": '4.8598', "s6": '87.0',"y":"143"}]

    ds = data.DataInput(data=input_data, schema=schema, convert=True)
    assert np.array_equal(ds.X[0], [59.0,2,32.1,101.0,157.0,93.2,38.0,4.0,4.8598,87.0])
    assert ds.Y[0] == 143.0

ds_schema = data.DataSchema(
        schema={
            "age": {"type": "number"},
            "sex": {"type": "category", "options": {1:"Male",2:"Female"}, "pre_convert":"number"},
            "bmi": {"type": "number"},
            "bp": {"type": "number"},
            "s1": {"type": "number"},
            "s2": {"type": "number"},
            "s3": {"type": "number"},
            "s4": {"type": "number"},
            "s5": {"type": "number"},
            "s6": {"type": "number"},
            "y": {"type": "number"}
        }, y_names=["y"]
    )
def test_create_input_dataset_returns_a_dataset_according_to_data_and_schema():
    input_data = {"diabetes_id": "1", "age": "59.0", "sex": "2", "bmi": "32.1", "bp": "101.0", "s1": '157.0', "s2": '93.2', "s3": '38.0', "s4": '4.0', "s5": '4.8598', "s6": '87.0'}

    ds = data.create_input_dataset(data=input_data, schema=ds_schema)
    assert np.array_equal(ds.X[0], [59.0,2,32.1,101.0,157.0,93.2,38.0,4.0,4.8598,87.0])

def test_create_dataset_returns_dataset_if_already_dataset():
    input_data = {"diabetes_id": "1", "age": "59.0", "sex": "2", "bmi": "32.1", "bp": "101.0", "s1": '157.0', "s2": '93.2', "s3": '38.0', "s4": '4.0', "s5": '4.8598', "s6": '87.0'}

    ds = data.create_input_dataset(data=input_data, schema=ds_schema)
    ds = data.create_input_dataset(data=ds, schema=ds_schema)
    assert np.array_equal(ds.X[0], [59.0,2.0,32.1,101.0,157.0,93.2,38.0,4.0,4.8598,87.0])

def test_create_dataset_handles_text_data():
    ds_schema = data.DataSchema(
        schema={
            "cxr_report": {"type": "string"},
            "notes": {"type": "string"},
            "crp": {"type": "number"},
            "score": {"type": "number"}
        }, y_names=["score"]
    )
    ds = data.SingleDataInput(data={"cxr_report": "consolidation", "notes": "pneumonia", "crp":101}, schema=ds_schema)
    assert ds.X_data["cxr_report"][0] == "consolidation"

def test_dataset_handles_boolean_nulls_data():
    ds_schema = data.DataSchema(
        schema={
            "x": {"type": "boolean","nullable":True},
            "score": {"type": "number"}
        }, y_names=["score"]
    )
    ds = data.SingleDataInput(data={"x":None}, schema=ds_schema)
    assert ds.X_data["x"][0] is None

