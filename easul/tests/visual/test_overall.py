import os
from unittest import mock

from easul import util

import pytest
from unittest.mock import Mock

from easul.driver import MemoryDriver
from easul.visual import Visual
from easul.tests.example import diabetes_progression_algorithm, EXAMPLE_PATH \
    # , diabetes_progression_dataset, complex_plan_data_with_ml
import logging

from easul.visual.element.overall import RocCurve, Accuracy, BalancedAccuracy, Matthews, Ppp, Npp, Specificity, \
    Sensitivity

logging.basicConfig(level = logging.INFO)
LOG = logging.getLogger(__name__)
import os

base_path = os.path.dirname(__file__) + "/"

import anys
import pytest
overall_elements = [
    (RocCurve,anys.AnyContains("data:image/png;base64")),
    (Accuracy, anys.AnyContains("75.00%")),
    (BalancedAccuracy, anys.AnyContains("49.62%")),
    (Matthews, anys.AnyContains("0.50")),
    (Ppp, anys.AnyContains("75.17%")),
    (Npp, anys.AnyContains("74.86%")),
    (Specificity, anys.AnyContains("78.74%")),
    (Sensitivity, anys.AnyContains("70.89%")),
]


@pytest.mark.parametrize("element_cls,expected_html", overall_elements)
def test_create_overall_elements(element_cls, expected_html):
    driver = MemoryDriver.from_reference("A1", autocreate=True)

    visual = Visual(elements=[
        element_cls()
    ], metadata_filename=EXAMPLE_PATH + "/metadata/model_scope.emd")

    html = visual.render(driver=driver)

    assert str(html) == expected_html

