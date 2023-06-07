
import os
from unittest import mock

from easul import util

from easul.driver import MemoryDriver
from easul.visual import Visual
from easul.tests.example import diabetes_progression_algorithm, prog_input_data, no_prog_input_data
import logging

from easul.visual.element import Prediction
from easul.visual.element.prediction import ProbabilityPlot, LimeTablePlot

logging.basicConfig(level = logging.INFO)
LOG = logging.getLogger(__name__)
from easul.tests.example import EXAMPLE_PATH

import anys
import pytest
prog_result = {"value":1,"label":"Progression", "probabilities":[{"value":0,"label":"No progression","probability":0.26},{"value":1,"label":"Progression","probability":0.74}]}
no_prog_result = {"value":0,"label":"No progression", "probabilities":[{"value":0,"label":"No progression","probability":0.67},{"value":1,"label":"Progression","probability":0.33}]}


row_simple_elements = [
    (ProbabilityPlot, anys.AnyContains("data:image/png;base64"), prog_result),
    (Prediction, anys.AnyContains("<h5>Progression</h5>"), prog_result),
    (Prediction, anys.AnyContains("<h5>No progression</h5>"), no_prog_result)
]

row_explain_elements = [
    (LimeTablePlot, anys.AnyContains("ldl, low-density lipoproteins</b> is less than 95.85"), prog_input_data),
    (LimeTablePlot, anys.AnyContains("ldl, low-density lipoproteins</b> is less than 95.85"), no_prog_input_data),
]

@pytest.mark.parametrize("element_cls,expected_html,result", row_simple_elements)
def test_create_simple_elements_for_ml(element_cls, expected_html, result):
    driver = MemoryDriver.from_reference("A1", autocreate=True)

    visual = Visual(elements=[
        element_cls()
    ], metadata_filename=EXAMPLE_PATH + "/metadata/row_scope.emd", algorithm=diabetes_progression_algorithm())

    html = visual.render(driver=driver, result=result)

    assert str(html) == expected_html

@pytest.mark.parametrize("element_cls,expected_html,input_data", row_explain_elements)
def test_create_explainable_elements_for_ml(element_cls, expected_html, input_data):
    driver = MemoryDriver.from_reference("A1", autocreate=True)

    visual = Visual(elements=[
        element_cls()
    ], metadata_filename=EXAMPLE_PATH + "/metadata/row_scope.emd", algorithm=diabetes_progression_algorithm())

    context = visual.generate_context(input_data=input_data)

    html = visual.render(driver=driver, context=context)

    assert str(html) == expected_html


def test_show_prediction_handles_expressions():
    driver = MemoryDriver.from_reference("A1", autocreate=True)
    algo = diabetes_progression_algorithm()

    visual = Visual(
            elements=[Prediction(title="Predicted amount",expression="value * 100",suffix="%",as_value=True)
    ], metadata_filename = EXAMPLE_PATH + "/metadata/row_scope.emd", algorithm = algo)

    result = algo.single_result(prog_input_data)
    html = visual.render(driver=driver, result=result)

    assert str(html) == anys.AnyContains("100.00%")


