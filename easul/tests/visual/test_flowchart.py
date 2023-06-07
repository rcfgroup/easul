import os
import logging
LOG = logging.getLogger(__name__)

from easul.driver import MemoryDriver

from unittest.mock import Mock
from easul.tests.fixtures import complex_plan
TEST_JOURNEY_CHART = "TEST_JOURNEY_CHART"
from anys import AnySearch
def test_journey_flowchart_within_plan(complex_plan):
    route = [
        "admission",
        "pneumonia_likelihood",
        "pneumonia_likely",
        "check_catheter",
        "pneumonia_escalation",
        "pneumonia_escalated"
    ]

    mock_chart = Mock()

    mock_chart.return_value.generate.return_value = TEST_JOURNEY_CHART

    driver = MemoryDriver.from_reference("A1", autocreate=True)
    flow_chart = complex_plan.steps["flowchart"]
    flow_chart.visual.elements[0].flowchart_cls = mock_chart
    assert flow_chart.render_visual(driver=driver, steps=complex_plan.steps, route=route) == AnySearch(TEST_JOURNEY_CHART)
