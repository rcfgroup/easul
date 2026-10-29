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

# ---------------------------------------------------------------------------
# copy_plan_with_new_sources - a copy must be self-consistent and leave the
# original alone. Steps refer to one another through DeferredItem proxies,
# which resolve against the plan they were created with, so sharing the steps
# (or shallow-copying them) sends the copied run back into the original plan,
# where the step sources were not replaced.
# ---------------------------------------------------------------------------

def _cap_plan_with_new_catheter_data(data):
    from easul.driver import MemoryDriver, LocalClock
    from easul.source import ConstantSource
    from easul.tests.example import complex_plan
    from easul.util import copy_plan_with_new_sources

    plan = complex_plan()
    plan_copy = copy_plan_with_new_sources(
        plan, {"catheter": ConstantSource(title="catheter", data=data)})

    driver = MemoryDriver.from_reference("SIM", autocreate=True, clock=LocalClock())
    plan_copy.run(driver)
    return plan, plan_copy, driver


def test_copy_plan_runs_through_its_own_steps():
    # The original catheter data scores below the threshold, so it discharges;
    # the simulated data scores above it, so the copy must reach ITU.
    _, __, driver = _cap_plan_with_new_catheter_data({"systolic_bp": 92})

    assert driver.get_route() == ["admission", "catheter_check", "itu"]


def test_copy_plan_does_not_share_steps_with_the_original():
    plan, plan_copy, _ = _cap_plan_with_new_catheter_data({"systolic_bp": 92})

    assert plan_copy.steps["catheter_check"] is not plan.steps["catheter_check"]


def test_copy_plan_steps_resolve_within_the_copy():
    from easul.util import DeferredItem

    _, plan_copy, _ = _cap_plan_with_new_catheter_data({"systolic_bp": 92})

    start = plan_copy.steps["admission"]
    assert isinstance(start.next_step, DeferredItem)
    assert start.next_step.plan is plan_copy


def test_copy_plan_leaves_the_original_sources_alone():
    from easul.tests.example import complex_plan
    from easul.util import copy_plan_with_new_sources
    from easul.source import ConstantSource

    plan = complex_plan()
    source = plan.steps["catheter_check"].source

    copy_plan_with_new_sources(
        plan, {"catheter": ConstantSource(title="catheter", data={"systolic_bp": 92})})

    assert plan.steps["catheter_check"].source is source
    assert source.data == {"systolic_bp": 80}


def test_copy_plan_leaves_the_original_runnable():
    from easul.driver import MemoryDriver, LocalClock
    from easul.source import ConstantSource
    from easul.tests.example import complex_plan
    from easul.util import copy_plan_with_new_sources

    plan = complex_plan()
    copy_plan_with_new_sources(
        plan, {"catheter": ConstantSource(title="catheter", data={"systolic_bp": 92})})

    driver = MemoryDriver.from_reference("ORIGINAL", autocreate=True, clock=LocalClock())
    plan.run(driver)

    assert driver.get_route() == ["admission", "catheter_check", "discharge"]
