
import re

from easul.data import DataSchema
from easul.decision import BinaryDecision
from easul.error import StepDataNotAvailable, NO_VISUAL_CONTEXT_MESSAGE, NO_VISUAL_RESULT_MESSAGE, NO_VISUAL_METADATA_MESSAGE
from easul.source import ConstantSource

from easul.step import NO_VISUAL_IN_STEP_MESSAGE, CheckEndStep
from easul.tests.example import complex_plan, prog_input_data, no_prog_input_data, complex_plan_with_ml
from easul.driver import MemoryDriver, LocalClock
import pytest
import logging
from datetime import datetime as dt
import anys

LOG = logging.getLogger(__name__)

from anys import ANY_DATETIME, AnySearch, ANY_LIST, ANY_DICT
import numpy as np

test_time = dt(2023,3,31,14,32)

test_plan_inputs = [
    ({"systolic_bp":92}, "A1", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp":92}, "A1B", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp":89}, "A2", ["admission","catheter_check","discharge"], {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"discharge"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp":None}, "A3", ["admission","catheter_check"], {'name': 'catheter_check', 'status': 'ERROR', 'outcome': None, 'timestamp': anys.ANY_DATETIME, 'result':None, 'next_step':None, 'value':None,'status_info': AnySearch(re.escape("[exception:{'systolic_bp': ['null value not allowed']}]"))}),
    ({"systolic_bp":""}, "A3", ["admission","catheter_check"], {'name': 'catheter_check', 'status': 'ERROR', 'outcome': None, 'timestamp': anys.ANY_DATETIME, 'next_step':None, 'status_info': AnySearch("Data invalid in step catheter_check"), 'result':None,'value':None})
]
from easul.util import copy_plan_with_new_sources

@pytest.fixture(scope="session")
def mock_plan():
    plan = complex_plan()
    plan.replace_source("catheter",{})
    return plan

@pytest.fixture(scope="session")
def mock_plan_with_ml():
    catheter_data = {"A1":{"systolic_bp":92},"A1B":{"systolic_bp":92}, "A2":{"systolic_bp":92},"A3":{"systolic_bp":92},"A4":{"systolic_bp":92},"A5":{"systolic_bp":95}}
    plan = complex_plan_with_ml()
    plan.replace_source("catheter", catheter_data)
   # plan.replace_source("progression", None)

    return plan

@pytest.fixture(scope="session")
def mock_plan_with_check_end():
    plan = complex_plan()
    plan.add_schema("discharge_check", DataSchema(schema={"discharged": {"type": "boolean"}}))
    from easul.algorithm import ExpressionAlgorithm
    from easul.expression import OperatorExpression
    import operator

    plan.add_step("discharge_check", CheckEndStep(
        title="Check discharge",
        algorithm=ExpressionAlgorithm(
            title="Likelihood of pneumonia based on CAP diagnosis",
            schema=plan.schemas["discharge_check"],
            expression=OperatorExpression(operator=operator.eq, input_field="discharged", value=True),
        ),
        source=plan.sources.get("discharge_check"),
        true_step=plan.steps.get("discharge")
    ))

    return plan

@pytest.mark.parametrize('input_data,reference,route,current_step',test_plan_inputs)
def test_complex_plan_drives_correctly_based_on_systolic_bp(mock_plan, input_data, reference, route, current_step):
    mock_plan.replace_source("catheter",{reference:input_data})
    from datetime import datetime as dt
    driver = MemoryDriver.from_reference(reference, autocreate=True, clock=LocalClock())
    mock_plan.run(driver)
    assert driver.get_route() == route #["admission","catheter_check","itu"]
    assert driver.get_current_journey_step() == current_step #{'name': 'itu', 'status': 'COMPLETE', 'outcome': None, 'timestamp': ANY_DATETIME, 'status_info': None}

def test_complex_plan_handles_reattempt_to_re_run(mock_plan):
    mock_plan.replace_source("catheter",{"A6":None})
    from datetime import datetime as dt
    driver = MemoryDriver.from_reference("A6", autocreate=True, clock=LocalClock())
    mock_plan.run(driver)
    mock_plan.run(driver)

    # assert driver.get_route() == route #["admission","catheter_check","itu"]
    # assert driver.get_current_journey_step() == current_step #{'name': 'itu', 'status': 'COMPLETE', 'outcome': None, 'timestamp': ANY_DATETIME, 'status_info': None}


def test_complex_plan_with_ml_model_waits_for_progression_data(mock_plan_with_ml):
    driver = MemoryDriver.from_reference("A1B", autocreate=True, clock=LocalClock())
    mock_plan_with_ml.run(driver)
    assert driver.get_current_journey_step() == {'name': 'progression_check', 'status': 'WAITING', 'outcome': None, 'timestamp': anys.ANY_DATETIME, 'status_info': 'Data not available in step progression_check', 'result':None, 'value':None,'next_step':None}

    assert driver.get_route() == ["admission","catheter_check","progression_check"]

pos_probs = [
    {'label': 'No progression','probability': 0.19,'value': 0},
    {'label': 'Progression','probability': 0.81,'value': 1}
]

neg_probs = [
    {'label': 'No progression','probability': 0.9,'value': 0},
    {'label': 'Progression','probability': 0.1,'value': 1}
]
test_ml_plan_inputs = [


    (prog_input_data, "A4",
     ["admission", "catheter_check", "progression_check", "progression_high","itu"],
     {'name': 'itu', 'status': 'COMPLETE', 'outcome': {'outcome_step': 'itu'}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None, 'value':None, 'next_step':None},
    {"progression_check":{'name': 'progression_check', 'next_step': 'progression_high', 'status': 'COMPLETE', 'outcome': {'next_step': 'progression_high', 'outcome_step': 'progression_check', 'reason': 'positive','result': {'data':ANY_DICT, 'label': 'Progression','value': 1, 'probabilities':pos_probs},'input_data':ANY_DICT, 'context':{'lime_table_plot':{'prediction_label':'Progression','reasons':ANY_LIST}}}, 'result':ANY_DICT, 'timestamp': anys.ANY_DATETIME,
     'status_info': None, 'value':1}},
     ),

    (no_prog_input_data, "A5",
     ["admission", "catheter_check", "progression_check", "progression_low", "discharge"],
     {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {'outcome_step': 'discharge'}, 'timestamp': anys.ANY_DATETIME, 'result':None, 'value':None,'next_step':None,
      'status_info': None},
 {"progression_check":{'name': 'progression_check', 'next_step': 'progression_low', 'status': 'COMPLETE', 'outcome': {'next_step': 'progression_low', 'outcome_step': 'progression_check', 'reason': 'negative','result': {'data':ANY_DICT,  'label': 'No progression','value': 0, 'probabilities':neg_probs},'input_data':ANY_DICT, 'context':{'lime_table_plot':{'prediction_label':'No progression', 'reasons':ANY_LIST}}}, 'result':ANY_DICT, 'timestamp': anys.ANY_DATETIME,
  'status_info': None, 'value':0}},
 )

]

@pytest.mark.parametrize('input_data,reference,route,current_step,expected_steps',test_ml_plan_inputs)
def test_complex_plan_with_ml_model_driven_correctly_for_progression_data(mock_plan_with_ml, input_data, reference, route, current_step, expected_steps):
    np.random.seed(123)
    mock_plan_with_ml.replace_source("progression",{reference:  input_data})
    driver = MemoryDriver.from_reference(reference, autocreate=True, clock=LocalClock())

    mock_plan_with_ml.run(driver)

    assert driver.get_route() == route
    assert driver.get_current_journey_step() == current_step

    for name, expected_step in expected_steps.items():
        assert driver.get_specific_step(name) == expected_step


test_ml_plan_layout_inputs = [
    (prog_input_data,"A4",r"71\.00.+What is the model rating.+data:image\/png;base64","Prediction.+<h5>Progression</h5>.+Probability plot.+data:image\/png;base64",{"value":1,"label":"Progression","probabilities":ANY_LIST, "data":ANY_DICT}),
    (no_prog_input_data,"A5","71\.00.+What is the model rating.+data:image\/png;base64","Prediction.+<h5>No progression</h5>.+Probability plot.+data:image\/png;base64",{"value":0,"label":"No progression","probabilities":ANY_LIST, "data":ANY_DICT})
]
@pytest.mark.parametrize('input_data,reference,expected_overview,expected_pred,expected_result',test_ml_plan_layout_inputs)
def test_complex_plan_with_ml_model_produces_correct_layout(mock_plan_with_ml, input_data, reference, expected_overview, expected_pred, expected_result):
    np.random.seed(123)
    mock_plan_with_ml.sources["progression"].source_data[reference] = input_data
    driver = MemoryDriver.from_reference(reference, autocreate=True, clock=test_time)

    mock_plan_with_ml.run(driver)

    observed_overview = mock_plan_with_ml.steps["overview"].render_visual(driver=driver, steps=mock_plan_with_ml.steps).replace("\n", "")
    assert observed_overview == AnySearch(expected_overview)

    observed_pred = mock_plan_with_ml.steps["progression_check"].render_visual(driver=driver, steps=mock_plan_with_ml.steps).replace("\n", "")

    assert observed_pred == AnySearch(expected_pred)
    bdata = driver.get_broker_data("outcome:progression_check")
    assert bdata["result"] == expected_result

def test_plan_handles_missing_visual(mock_plan_with_ml):
    np.random.seed(123)
    mock_plan_with_ml.sources["progression"].source_data["A4"] = prog_input_data
    driver = MemoryDriver.from_reference("A4", autocreate=True, clock=LocalClock())

    mock_plan_with_ml.run(driver)

    assert mock_plan_with_ml.steps["progression_low"].render_visual(driver=driver, steps=mock_plan_with_ml.steps) == AnySearch(NO_VISUAL_IN_STEP_MESSAGE)

def test_plan_handles_visual_with_missing_result(mock_plan_with_ml):
    from easul.util import copy_plan_with_new_sources
    plan_copy = copy_plan_with_new_sources(mock_plan_with_ml, {
        "progression":ConstantSource(title="Prog data", data={}),
        "catheter":ConstantSource(title="Cath data",data={"systolic_bp":120})
    })
    np.random.seed(123)

    # plan_copy = .replace_source("progression",{"A4": prog_input_data})
    driver = MemoryDriver.from_reference("A4", autocreate=True, clock=test_time)
    plan_copy.run(driver)
    # driver._broker._store["outcome:progression_check"]["A4"]["result"] = None
    assert plan_copy.steps["progression_check"].render_visual(driver=driver, steps=mock_plan_with_ml.steps) == AnySearch(NO_VISUAL_RESULT_MESSAGE)

def test_plan_handles_visual_with_missing_metadata():
    from easul.tests.example import complex_plan_with_ml
    plan = complex_plan_with_ml()
    plan.replace_source("catheter",{})
    plan.replace_source("progression",{"A1": prog_input_data})

    driver = MemoryDriver.from_reference("A1", autocreate=True, clock=test_time)
    plan.steps["overview"].visual.metadata.clear()

    assert plan.steps["overview"].render_visual(driver=driver, steps=plan.steps) == NO_VISUAL_METADATA_MESSAGE

def test_plan_handles_visual_with_missing_context(mock_plan_with_ml):
    mock_plan_with_ml.sources["progression"].source_data["A1"] = prog_input_data
    driver = MemoryDriver.from_reference("A1", autocreate=True, clock=test_time)
    mock_plan_with_ml.run(driver)
    driver._broker._store["outcome:progression_check"]["A1"]["context"] = None

    assert mock_plan_with_ml.steps["progression_check"].render_visual(driver=driver, steps=mock_plan_with_ml.steps) == AnySearch(NO_VISUAL_CONTEXT_MESSAGE)

def test_plan_handles_visual_with_missing_context(mock_plan_with_ml):
    plan_copy = copy_plan_with_new_sources(mock_plan_with_ml, {
        "progression":ConstantSource(title="prog",data=prog_input_data),
        "catheter":ConstantSource(title="cath", data={"systolic_bp":92})
    })
    driver = MemoryDriver.from_reference("A1", autocreate=True, clock=test_time)
    plan_copy.run(driver)
    driver._client._journeys["A1"]["steps"][2]["outcome"]["context"] = None

    assert plan_copy.steps["progression_check"].render_visual(driver=driver, steps=mock_plan_with_ml.steps) == AnySearch(NO_VISUAL_CONTEXT_MESSAGE)

test_end_step_plan_inputs = [
    ({"systolic_bp":92}, None, "A1", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp":92}, {"discharged":False}, "A1B", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp": 92}, {"discharged": True}, "A1B", ["discharge_check", "discharge"],
     {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {
         "outcome_step": "discharge"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result': None, 'value': None,
      'next_step': None}),
    ({"systolic_bp":89}, {"discharged":True}, "A2", ["discharge_check", "discharge"], {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"discharge"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
]

@pytest.mark.parametrize('cath_data,dis_data, reference,route,current_step',test_end_step_plan_inputs)
def test_does_not_record_check_end_step_if_data_not_found(mock_plan_with_check_end, cath_data, dis_data, reference, route, current_step):
    driver = MemoryDriver.from_reference(reference, autocreate=True, clock=LocalClock())
    plan_copy = copy_plan_with_new_sources(mock_plan_with_check_end, {
        "progression": ConstantSource(title="prog", data=prog_input_data),
        "catheter": ConstantSource(title="cath", data={"systolic_bp": 92}),
        "discharge_check": ConstantSource(title="Discharge check", data=dis_data)
    })
    plan_copy.steps["discharge_check"].source = plan_copy.sources["discharge_check"]
    # mock_plan_with_check_end.replace_source("discharge_check", {reference: dis_data})
    # mock_plan_with_check_end.steps["discharge_check"] = mock_plan_with_check_end.sources["discharge_check"]
    plan_copy.run(driver)
    assert driver.get_route() == route
    assert driver.get_current_journey_step() == current_step

test_end_step_plan_inputs = [
    ({"systolic_bp":92}, None, "A1", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp":92}, {"discharged":False}, "A1B", ["admission","catheter_check","itu"], {'name': 'itu', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"itu"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
    ({"systolic_bp": None}, {"discharged": True}, "A1B", ["admission", "catheter_check", "discharge_check", "discharge"],
     {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {
         "outcome_step": "discharge"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result': None, 'value': None,
      'next_step': None}),
    (None, {"discharged":True}, "A2", ["admission","catheter_check", "discharge_check", "discharge"], {'name': 'discharge', 'status': 'COMPLETE', 'outcome': {
        "outcome_step":"discharge"}, 'timestamp': anys.ANY_DATETIME, 'status_info': None, 'result':None,'value':None,'next_step':None}),
]

@pytest.mark.parametrize('cath_data,dis_data, reference,route,current_step',test_end_step_plan_inputs)
def test_checks_end_step_at_beginning_of_different_runs(mock_plan_with_check_end, cath_data, dis_data, reference, route, current_step):
    plan_copy = copy_plan_with_new_sources(mock_plan_with_check_end, {
        "progression":ConstantSource(title="prog",data=None),
        "catheter": ConstantSource(title="cath", data=cath_data),
        "discharge_check": ConstantSource(title="Discharge check", data=None)
    })
    driver = MemoryDriver.from_reference(reference, autocreate=True, clock=LocalClock())
    # mock_plan_with_check_end.replace_source("catheter", {reference: cath_data})
    # dis_source = ConstantSource(title="Discharge check", data=None)
    # mock_plan_with_check_end.add_source("discharge_check", dis_source)
    # mock_plan_with_check_end.steps["discharge_check"].source = dis_source
    plan_copy.run(driver)

    dis_source2 = ConstantSource(title="Discharge check", data=dis_data)
    plan_copy.add_source("discharge_check", dis_source2)
    plan_copy.steps["discharge_check"].source = dis_source2
    plan_copy.run(driver)

    assert driver.get_route() == route
    assert driver.get_current_journey_step() == current_step