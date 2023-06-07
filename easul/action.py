"""

"""
import logging

from easul.algorithm.result import DefaultResult
from easul.outcome import ResultOutcome

LOG = logging.getLogger(__name__)
from attrs import define, field

class StopFlow(Exception):
    pass

@define(kw_only=True)
class Action:
    """
    Base Action class. Actions enable things to occur at different points in steps (e.g. before the run, following invalid data).
    """
    def before_run(self, *args, **kwargs):
        pass

    def after_run(self, *args, **kwargs):
        pass

    def invalid_data(self, *args, **kwargs):
        pass

    def missing_data(self, *args, **kwargs):
        pass

    def after_data(self, *args, **kwargs):
        pass

    def describe(self):
        return {
            "type":self.__class__.__name__
        }

@define(kw_only=True)
class ResultStoreAction(Action):
    """
    Action which stores a result in the broker once an outcome has been obtained.
    Result data is stored with an outcome prefix (e.g. outcome:[step-name])
    """
    data_source:str = "easul"
    decision_steps = field(factory=list)
    send_message = field(default=False)

    def after_run(self, event):
        if self.decision_steps and event.outcome.next_step.name not in self.decision_steps:
            return

        data = event.outcome.input_data.asdict() if hasattr(event.outcome, "input_data") else {}
        data["result"] = event.outcome.result.asdict() if hasattr(event.outcome, "result") else None

        if not event.outcome.context:
            context = None
        else:
            context = event.outcome.context if type(event.outcome.context) is dict else event.outcome.context.asdict()

        data["context"] = context

        event.driver.store_data_in_broker(reference=event.driver.journey["reference"], data_type="outcome:" + event.outcome.outcome_step.name, data = data, external=True, send_message=self.send_message)


@define(kw_only=True)
class CompleteJourneyAction(Action):
    """
    Action which completes a journey following the run.
    """
    def after_run(self, event):
        event.driver._client.complete_journey(reference=event.driver.journey["reference"])
        event.driver.journey["complete"]=1



@define(kw_only=True)
class PassPreviousResultAction(Action):
    """
    Action which puts the previous outcome value into the input data.
    """
    as_field = field()

    def after_data(self, event):
        if event.previous_outcome:
            event.data[self.as_field] = event.previous_outcome.value


@define(kw_only=True)
class PreRunStateAction(Action):
    """
    Action which updates a state with a new value following the run.
    """
    state = field()
    state_value = field()

    def after_run(self, event):
        event.driver.store_state(self.state.label, self.state_value, event.step.name)


@define(kw_only=True)
class IgnoreMissingData(Action):
    """
    Action which handles missing data and sets an outcome with a default value.
    """
    default_value = field()
    next_step = field()

    def missing_data(self, event):
        event.outcome = ResultOutcome(outcome_step=event.step, input_data=event.data, next_step = self.next_step, reason="Missing data", result=DefaultResult(value=None, data=self.default_value), value=self.default_value)

@define(kw_only=True)
class IgnoreMissingTimebasedData(IgnoreMissingData):
    """
    Action which handles missing data and sets a timestamp in the outcome.
    """
    timestamp_field = field()

    def missing_data(self, event):
        values = self.default_value
        values[self.timestamp_field] = event.driver.clock.timestamp
        event.outcome = ResultOutcome(outcome_step=event.step, input_data=event.data, next_step = self.next_step, reason="Missing data", result=DefaultResult(value=None, data=values), value=values)