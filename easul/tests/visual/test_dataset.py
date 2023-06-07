import easul.driver
import easul.engine
from easul.visual import Visual
from unittest.mock import Mock
from easul.visual.element.journey import JourneyMap
from easul.visual.draw.flowchart import MermaidWebFlowChart
TEST_JOURNEY_CHART = "TEST_JOURNEY_CHART"
from anys import AnySearch

def test_dataset_journeychart_rendering(complex_plan):
    mock_chart = Mock()

    mock_chart.return_value.generate.return_value = TEST_JOURNEY_CHART
    vs = Visual(elements=[JourneyMap(start_step="admission")])
    vs.elements[0].flowchart_cls = mock_chart

    driver = easul.driver.MemoryDriver.from_reference("A1", autocreate=True)
    step = Mock()
    step.name = "test"
    assert vs.render(driver=driver, step=step, steps=complex_plan.steps) == AnySearch(TEST_JOURNEY_CHART)