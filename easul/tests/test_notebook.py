from easul.examples import create_example_plan
from easul import *
from easul.visual.render import PlainRenderer

class MockRenderer(PlainRenderer):
    """
    Modifies PlainRenderer to return rendered data - so it can be tested against expected values.
    """
    def render(self, data):
        return data

renderer = MockRenderer()

def test_copy_plan():
    plan = create_example_plan()

    input_data = {"catheter":{"sbp":120},
                 "progression":{"age": 59, "sex": 2, "bmi": 32.1, "bp": 101, "s1": 157, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9, "s6": 87}
                  }
    from copy import copy
    from easul.plan import Plan

    from easul.driver import MemoryDriver, LocalClock
    driver = MemoryDriver.from_reference(reference="SIMULATE", autocreate=True, clock=LocalClock())

    new_sources = {}

    from easul.util import DeferredCatalog
    for name, source_data in input_data.items():
        original_source = plan.sources.get(name)
        new_sources[name] = StaticSource(title=original_source.title, processes=original_source.processes,
                                                source_data={"SIMULATE":source_data})

    plan_copy = Plan(
        title=plan.title,
        sources=DeferredCatalog(new_sources),
        schemas=copy(plan.schemas),
        visuals=copy(plan.visuals),
        algorithms=copy(plan.algorithms),
        steps=copy(plan.steps),
        states=copy(plan.states),
        config=copy(plan.config)
    )

    for name, step in plan_copy.steps.items():
        if hasattr(step,"source") and step.source:
            step.source = plan_copy.sources.get(step.source.name)


def refresh_sources(refresh_plan):
    pass

def test_visualise_step():
    from easul.examples import create_example_plan
    from easul.notebook import visualise_step
    plan = create_example_plan()

    assert "label.easul" in visualise_step(step_name="progression_check",plan=plan, input_data={"catheter": {"systolic_bp": 120},
                                                  "progression": {"age": 59, "sex": 2, "bmi": 32.1, "bp": 101,
                                                                  "s1": 157, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9,
                                                                  "s6": 87}}, renderer=renderer)

def test_visualise_plan():
    from easul.examples import create_example_plan
    from easul.notebook import visualise_plan

    plan = create_example_plan()
    visualise_plan(plan, renderer=renderer)


def test_describe_step():
    from easul.examples import create_example_plan
    from easul.notebook import describe_step

    plan = create_example_plan()
    assert "<table><tr>" in describe_step("progression_check",plan, renderer=renderer)


def test_describe_plan():
    from easul.examples import create_example_plan
    from easul.notebook import describe_plan

    plan = create_example_plan()
    assert "<table><tr>" in describe_plan(plan, renderer=renderer)


def test_simulate_decision():
    from easul.examples import create_example_plan
    from easul.notebook import simulate_decision

    plan = create_example_plan()

    assert "<td>age</td><td>62.0</td>" in simulate_decision("progression_check", plan,input_data={"catheter": {"systolic_bp": 120},
                                                  "progression": {"age": 62, "sex": 2, "bmi": 32.1, "bp": 101,
                                                                  "s1": 157, "s2": 93.2, "s3": 38, "s4": 4, "s5": 4.9,
                                                                  "s6": 87}}, renderer=MockRenderer())

    data = simulate_decision("progression_check", plan,
                                                       input_data={"catheter": {"systolic_bp": 120},
                                                                   "progression": {"age": 23, "sex": 2, "bmi": 32.1,
                                                                                   "bp": 101,
                                                                                   "s1": 157, "s2": 93.2, "s3": 38,
                                                                                   "s4": 4, "s5": 4.9,
                                                                                   "s6": 87}}, renderer=MockRenderer(), as_data=True)

    assert data["result"]["data"]["age"]==23






