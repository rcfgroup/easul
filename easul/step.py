from attrs import define, field
import logging

from easul.decision import BinaryDecision

LOG = logging.getLogger(__name__)

from easul.error import StepDataNotAvailable, ConversionError, InvalidStepData, VisualDataMissing, ValidationError
from enum import Enum, auto

from easul.outcome import Outcome, EndOutcome, PauseOutcome, InvalidDataOutcome, MissingDataOutcome
from abc import abstractmethod

NO_VISUAL_IN_STEP_MESSAGE = "Sorry no visual for this step"

@define(kw_only=True)
class Step:
    """
    Base Step class. Steps are the driving force of plans, they bring the different components together.
    The key things are 'visual' components which provide graphical views associated with steps and 'actions' which
    define action classes that occur during the lifecycle of a step run.
    """
    title = field()
    visual = field(default=None)
    exclude_from_chart = field(default=False)
    name = field(default=None)
    actions = field(factory=list)

    def layout_kwargs(self, driver, steps, **kwargs):
        return {"steps":steps, "driver":driver, "step":self, **kwargs}

    def render_visual(self, driver: "easul.driver.Driver", steps, result=None, context=None, renderer=None, **kwargs):
        """
        Render visual to HTML utilising the data in the broker (if not supplied) and the supplied renderer
        Args:
            driver:
            steps:
            result:
            context:
            renderer:
            **kwargs:

        Returns:

        """
        if not self.visual:
            return NO_VISUAL_IN_STEP_MESSAGE


        if not result and not context:
            b_data = driver.get_broker_data("outcome:" + self.name)

            if b_data:
                result = b_data.get("result")
                context = b_data.get("context")

        try:
            return self.visual.render(driver=driver, steps=steps, step=self, result=result, context=context, renderer=renderer)
        except VisualDataMissing as ex:
            return str(ex)

    @property
    def possible_links(self):
        return {}

    @property
    def data_sources(self):
        return []


    def _trigger_actions(self, trigger_type, event):
        for action in self.actions:
            getattr(action, trigger_type)(event)

    def _generate_visual_context(self, data):
        return self.visual.generate_context(data) if self.visual else None

    def __repr__(self):
        return self.name

    def describe(self):
        """
        Describe step as Python data structures (lists and dicts)
        Returns:

        """
        return {
            "name": self.name,
            "title": self.title,
            "actions": [a.describe() for a in self.actions],
            "visual":self.visual.describe() if self.visual else "N/A"
        }

@define(kw_only=True)
class VisualStep(Step):
    """
    Visual focussed step.
    """
    exclude_from_chart = True
    requires_journey = field(default=True)

@define(kw_only=True)
class ActionEvent:
    """
    Event object fed to Action classes to enable access to steps, data, outcome and drivers.
    """
    step = field()
    driver = field()
    previous_outcome = field(default=None)
    data = field(default=None)
    outcome = field(default=None)


@define(kw_only=True)
class ActionStep(Step):
    """
    Step which involves action based on data from a 'source'
    """
    source = field(default=None)

    def run_all(self, driver, previous_outcome=None):
        event = ActionEvent(step=self, driver=driver, previous_outcome=previous_outcome)
        self._trigger_actions("before_run", event)
        driver.store_step(self.name, StepStatuses.INIT, timestamp=driver.clock.timestamp)

        from easul.plan import run_step_logic

        return run_step_logic(self, event)

    @abstractmethod
    def _determine_outcome(self, event):
        pass

    def _retrieve_data(self, event):
        from easul.data import DataInput
        data = self.source.retrieve(event.driver, self)
        return DataInput(data, schema=None, convert=False, validate=False)

    def _store_current(self, driver, reason):
        driver.store_state(self.state.label, self.state_value, reason, self.name, timestamp=driver.clock.timestamp)
        driver.store_step(self.name, StepStatuses.INIT, timestamp=driver.clock.timestamp)

    def run_logic(self, event):
        """
        Runs the logic part of the step lifecycle to determine the outcome.

        Args:
            event:

        Returns:

        """
        outcome = self._determine_outcome(event)
        event.driver.store_step(self.name, StepStatuses.COMPLETE, outcome=outcome, timestamp=event.driver.clock.timestamp)
        return outcome

    def layout_kwargs(self, driver, steps, **kwargs):
        return {}

    def describe(self):
        desc = super().describe()
        desc.update({"source": self.source.describe() if self.source else "N/A"})
        return desc

@define(kw_only=True)
class EndStep(ActionStep):
    """
    End step in journey. Results in completion of journey.
    """
    def __attrs_post_init__(self):
        from easul.action import CompleteJourneyAction
        self.actions.append(CompleteJourneyAction())

    def _determine_outcome(self, event):
        return EndOutcome(outcome_step=self)


@define(kw_only=True)
class AlgorithmStep(ActionStep):
    """
    Step which enables algorithms to be embedded into decisions. Uses the 'source' to retrieve and process data.
    Feeds the data into the 'algorithm' to get a result which is fed into a 'decision' to determine an outcome.
    """
    source = field()
    algorithm = field()
    decision = field()

    def describe(self):
        desc = super().describe()
        desc.update({
            "decision": self.decision.describe(),
            "algorithm": self.algorithm.describe()
        })
        return desc

    def _determine_outcome(self, event):
        data = self._retrieve_data(event)
        result, context = self._run_algorithm(data, event.driver)
        return self.decision.decide_outcome(result=result, context=context, data=data, step=self)

    def _run_algorithm(self, data, driver):
        algorithm = self.algorithm

        result = algorithm.single_result(data)
        context = self._generate_visual_context(data)

        return result, context

    def _retrieve_data(self, event):
        if not self.source:
            LOG.warning(f"No source specified in step '{self.name}' so cannot retrieve data")
            raise InvalidStepData(journey=event.driver.journey, step_name=self.name, exception=SystemError(f"No source specified in step '{self.name}' so cannot retrieve data"))

        event.data = self.source.retrieve(event.driver, self)
        self._trigger_actions("after_data", event)

        if not event.data:
            raise StepDataNotAvailable(journey=event.driver.journey, step_name=self.name)

        try:
            return self.algorithm.create_input_dataset(event.data)
        except ConversionError as ex:
            raise InvalidStepData(journey=event.driver.journey, step_name=self.name, exception=ex.orig_exception)
        except ValidationError as ex:
            raise InvalidStepData(journey=event.driver.journey, step_name=self.name, exception=ex)

    @property
    def possible_links(self):
        return self.decision.possible_links

    @property
    def data_sources(self):
        return self.source.source_titles


@define(kw_only=True)
class PreStep(ActionStep):
    """
    Step which precedes another one.

    NB. It may include extraction of source data but this is simply added to the outcome
    without requiring a decision to be made.
    """
    next_step: Step = field()

    def _determine_outcome(self, event):
        if self.source:
            data = self._retrieve_data(event)
        else:
            data = None

        return Outcome(outcome_step=self, next_step=self.next_step, reason="next", input_data=data)

    @property
    def possible_links(self):
        return {"next": self.next_step}

    def describe(self):
        desc = super().describe()
        desc.update({
            "next_step": self.next_step.title
        })
        return desc

@define(kw_only=True)
class PauseStep(ActionStep):
    """
    Step which indicates that the process should be paused. Used to prevent runs from getting into iterative loops.
    """
    next_step: Step = field()

    def _determine_outcome(self, event):
        event.driver.store_step(self.name, StepStatuses.PAUSE, status_info="Paused for next time transition", timestamp=event.driver.clock.timestamp)
        return PauseOutcome(outcome_step=self, next_step=self.next_step, reason="next", input_data=None)

    @property
    def possible_links(self):
        return {"next": self.next_step}

    def describe(self):
        desc = super().describe()
        desc.update({
            "next_step": self.next_step.title
        })
        return desc

@define(kw_only=True)
class StartStep(PreStep):
    """
    Start step in journey. The run logic searches for this to determine where the run should start.
    """
    pass

@define(kw_only=True)
class CheckEndStep(AlgorithmStep):
    """
    Embedded step which is executed whenever a specific journey is resumed. For example, it can check if a patient
    has already been discharged.
    """
    true_step = field()
    decision = field(init=False)

    @decision.default
    def _default_decision(self):
        return BinaryDecision(true_step=self.true_step, false_step=None)

    def run_all(self, driver, previous_outcome=None):
        event = ActionEvent(step=self, driver=driver, previous_outcome=previous_outcome)
        self._trigger_actions("before_run", event)

        try:
            outcome = self._determine_outcome(event)
            event.outcome = outcome
            self._trigger_actions("after_run", event)

            if outcome.next_step is not None:
                event.driver.store_step(self.name, StepStatuses.COMPLETE, outcome=outcome,
                                     timestamp=event.driver.clock.timestamp)

            return outcome

        except StepDataNotAvailable as ex:
            return MissingDataOutcome(outcome_step=self, reason=str(ex))

        except InvalidStepData as ex:
            return InvalidDataOutcome(outcome_step=self, reason=str(ex))

    def describe(self):
        desc = super().describe()
        desc.update({
            "true_step": self.true_step.title,
            "decision":self.decision.describe()
        })
        return desc


class StepStatuses(Enum):
    """
    Enum containing statuses which match those used within the client.
    """
    INIT = auto()
    WAITING = auto()
    COMPLETE = auto()
    PENDING = auto()
    ERROR = auto()
    PAUSE = auto()


