from easul.source import ConstantSource
from easul import DeferredItem
from easul.tests.example import *

import logging

from easul.visual.element.journey import JourneyMap

LOG = logging.getLogger(__name__)

def test_simple_plan_is_instantiated():
    from easul.plan import Plan
    from easul.state import State
    from easul.step import EndStep, StartStep
    from easul.action import PreRunStateAction
    plan = Plan(title="CAP")
    plan.add_state("admission_state", State(label="admission", default=None))

    plan.add_step("discharge", EndStep(
        title="End",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="discharged")]
    ))
    plan.add_step("admission", StartStep(
        title="Patient admission",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="admitted")],
        next_step=plan.get_step("discharge")
    ))
    plans = {"cap":plan}

    assert isinstance(plans["cap"], Plan)
    start = plans["cap"].steps["admission"]
    end = plans["cap"].steps["discharge"]

    assert isinstance(start, StartStep)
    assert start.next_step == end

    adm_state = plans["cap"].states["admission_state"]
    assert start.actions[0].state == adm_state
    assert isinstance(adm_state, State)
    assert start.actions[0].state_value == "admitted"

def test_complex_plan_is_instantiated():
    from easul.plan import Plan
    from easul.state import State
    from easul.step import EndStep, StartStep,Step, AlgorithmStep
    from easul.decision import BinaryDecision
    from easul.visual import Visual

    from easul.action import PreRunStateAction
    plan = Plan(title="CAP")
    plan.add_state("admission_state", State(label="admission", default=None))

    plan.add_step("discharge", EndStep(
        title="Discharge",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="discharged")]
    ))
    plan.add_step("itu", EndStep(
        title="ITU",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="itu")]
    ))

    plan.add_step("admission", StartStep(
        title="Patient admission",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="admitted")],
        next_step=plan.get_step("catheter_check")
    ))

    plan.add_step("flowchart", Step(
        title="CAP logic map",
        visual=Visual(
        elements=[
            JourneyMap(route_only=False, start_step="admission")
        ]),
        exclude_from_chart=True
    ))

    plan.add_schema("catheter",
                    DataSchema(
                        schema={
                            "systolic_bp": {"type": "number"},
                            "score": {"type": "number"}
                        },
                        y_names=["score"]
                    )
                    )

    from easul.algorithm import ScoreAlgorithm
    plan.add_algorithm("catheter",
                       ScoreAlgorithm(
                           title="Catheter algorithm",
                           schema=plan.get_schema("catheter"),
                           factors=OperatorFactor(title="High BP", operator=operator.gt, input_field="systolic_bp", value=90, penalty=1)
                       )
                       )
    plan.add_step("catheter_check", AlgorithmStep(
        title="Catheter check",
        actions=[PreRunStateAction(state=plan.get_state("admission_state"), state_value="catheter_check")],
        algorithm=plan.get_algorithm("catheter"),
        source=plan.get_source("catheter"),
        decision=BinaryDecision(
            true_step=plan.get_step("itu"),
            false_step=plan.get_step("discharge")
        )
    ))

    plan.add_source("catheter", ConstantSource(title="Catheter data", data={"systolic_bp": 95}))

    from easul.plan import Plan
    from easul import step, state
    plans = {"cap":plan}
    assert isinstance(plans["cap"], Plan)
    start = plans["cap"].steps["admission"]
    catheter = plans["cap"].steps["catheter_check"]

    assert isinstance(start, step.StartStep)
    assert start.next_step.source == catheter.source
    assert id(start.next_step.source) == id(catheter.source)
    adm_state = plans["cap"].states["admission_state"]
    assert start.actions[0].state == adm_state
    assert id(start.actions[0].state) == id(adm_state)
    assert isinstance(adm_state, state.State)
    assert start.actions[0].state_value == "admitted"


def test_recursive_data_plan_is_instantiated():
    from easul.plan import Plan
    from easul.state import State
    from easul.step import PreStep, StartStep, PauseStep

    plan = Plan(title="CAP")
    plan.add_state("admission_state", State(label="admission", default=None))

    plan.add_step("pause", PauseStep(
        title="Pause",
        next_step=DeferredItem(plan=plan, name="check", property="steps")
    ))
    plan.add_step("check", PreStep(
        title="check",
        next_step=DeferredItem(plan=plan, name="pause", property="steps")
    ))
    plan.add_step("admission", StartStep(
        title="Patient admission",
        next_step=plan.get_step("check")
    ))

    plans = {"cap": plan}

    assert isinstance(plans["cap"], Plan)
    start = plans["cap"].steps["admission"]
    check = plans["cap"].steps["check"]
    pause = plans["cap"].steps["pause"]

    assert isinstance(start, StartStep)
    assert start.next_step == check
    assert check.next_step == pause
    assert pause.next_step == check
