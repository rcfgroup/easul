from typing import Dict

from attrs import define, field
import logging

from easul.source import LOG, StaticSource, CollatedSource
from easul.step import ActionEvent, CheckEndStep, StepStatuses, Step
from easul.util import DeferredItem,DeferredCatalog,is_successful_outcome, get_start_step

LOG = logging.getLogger(__name__)
from easul.run import run_step_chain

@define(kw_only=True)
class Plan:
    """
    Core class for handling Plans.
    which includes re-usable/replaceable steps, sources, algorithms, schemas, visuals and states.
    """
    title = field()
    steps:Dict[str, Step] = field(factory=DeferredCatalog)
    sources = field(factory=DeferredCatalog)
    algorithms = field(factory=DeferredCatalog)
    schemas = field(factory=DeferredCatalog)
    visuals = field(factory=DeferredCatalog)
    states = field(factory=DeferredCatalog)
    config = field(factory=DeferredCatalog)
    _check_steps = field(init=False)

    @_check_steps.default
    def default_check_steps(self):
        return list(filter(lambda x: isinstance(x, CheckEndStep), self.steps.values()))

    def _check_steps_for_end(self, driver):
        for cs in self._check_steps:
            cs.run_all(driver=driver)

    def run(self, driver):
        """
        Run plan for driver-based on a specific journey.
        Args:
            driver:

        Returns:

        """
        from easul.step import StepStatuses
        steps = self.steps

        if driver.journey.get("complete") == 1:
            LOG.info(f"Journey '{driver.journey.get('reference')}' is already complete")
            return

        self._check_steps_for_end(driver)

        current_journey_step = driver.get_current_journey_step()

        if current_journey_step is None:
            next_step = get_start_step(steps)
            step_status = StepStatuses.INIT.name
        else:
            step_status = current_journey_step["status"]
            next_step = steps[current_journey_step["name"]]

        if step_status in [StepStatuses.WAITING.name]:
            event = ActionEvent(step=next_step, driver=driver, previous_outcome=None)
            outcome = run_step_logic(next_step,event)
            if is_successful_outcome(outcome) is False:
                return

            next_step = outcome.next_step
        elif step_status == StepStatuses.COMPLETE.name:
            journey_step_outcome = current_journey_step["outcome"]
            if journey_step_outcome:
                next_step_name = current_journey_step.get("next_step")
                if next_step_name is None:
                    LOG.warning(f"No next step in journey from previous outcome")
                    next_step = None
                else:
                    next_step = steps.get(next_step_name)

            else:
                next_step = None

            if not next_step:
                self._mark_complete(driver)
                return

        run_step_chain(next_step, driver)

    def _mark_complete(self, driver):
        LOG.info(f"Journey marked complete [{driver.journey['reference']}]")
        driver._client.mark_complete(reference=driver.journey["reference"])

    def run_from(self, step_name:str, driver:"easul.driver.Driver"):
        """
        Run plan for driver-based on a specific journey from a particular step
        Args:
            step_name: name of step
            driver:

        Returns:

        """
        from_step = self.steps.get(step_name)
        run_step_chain(from_step, driver)

    def add_step(self, name:str, step):
        step.name = name

        self.steps[name] = step
        self._check_steps = self.default_check_steps()


    def get_or_defer_property(self, property, name):
        if name not in getattr(self, property):
            return DeferredItem(plan=self, property=property, name=name)

        return getattr(self, property)[name]

    def get_property(self, property, name=None):
        if not name:
            return getattr(self, property)

        try:
            return getattr(self, property)[name]
        except KeyError:
            raise SystemError(f"There is no '{name}' present in '{property}'")

    def get_step(self, name:str):
        return self.get_or_defer_property("steps", name)

    def add_state(self, name:str, state):
        self.states[name] = state

    def get_state(self, name:str):
        return self.get_or_defer_property("states", name)

    def add_schema(self, name:str, schema):
        self.schemas[name] = schema

    def get_schema(self, name:str):
        return self.get_or_defer_property("schemas", name)

    def add_algorithm(self, name:str, algorithm):
        self.algorithms[name] = algorithm

    def get_algorithm(self, name:str):
        return self.get_or_defer_property("algorithms", name)

    def add_source(self, name:str, source):
        self.sources[name] = source

    def get_source(self, name:str):
        return self.get_or_defer_property("sources", name)

    def add_visual(self, name:str, visual):
        self.visuals[name] = visual

    def get_visual(self, name:str):
        return self.get_or_defer_property("visuals", name)

    def replace_source(self, name, source):
        actual_source = self.sources.get(name)
        if not actual_source:
            raise SystemError(f"Actual source '{name}' does not exist in plan")

        if isinstance(source, CollatedReplace):
            replace_sources = actual_source.sources

            for sub_source_name, sub_source in source.kwargs.items():
                if not sub_source_name in replace_sources:
                    raise ValueError(f"Replacement source name '{sub_source_name} does not exist in the collated source")

                replace_actual_source = replace_sources[sub_source_name]
                print(f"replace_actual_source:{replace_actual_source}")
                replace_sources[sub_source_name] = StaticSource(source_data ={source.reference:sub_source}, title= replace_actual_source.title + "_" + sub_source_name, processes= replace_actual_source.processes)

            self.sources[name] = CollatedSource(sources = replace_sources,title= actual_source.title, processes = actual_source.processes)
        else:
            self.sources[name] = StaticSource(source_data=source, title = actual_source.title, processes = actual_source.processes)


class CollatedReplace:
    def __init__(self, reference, **kwargs):
        self.reference = reference
        self.kwargs = kwargs

def run_step_logic(step, event):
    """
    Main function used by
    Args:
        step: Step to run
        event: ActionEvent passed in

    Returns:

    """
    from easul.error import StepDataNotAvailable, InvalidStepData
    from easul.outcome import MissingDataOutcome, InvalidDataOutcome

    try:
        outcome = step.run_logic(event)
        event.outcome = outcome
        step._trigger_actions("after_run", event)
        return outcome
    except StepDataNotAvailable as ex:
        LOG.warning(f"[{ex.journey.get('reference')}:{step.name}] step data NOT available [status:WAITING]")
        event.driver.store_step(step.name, StepStatuses.WAITING, status_info=str(ex), timestamp=event.driver.clock.timestamp)
        step._trigger_actions("missing_data", event)
        if event.outcome:
            return event.outcome

        return MissingDataOutcome(outcome_step=step, reason=str(ex))

    except InvalidStepData as ex:
        step._trigger_actions("invalid_data", event)
        if event.outcome:
            return event.outcome

        LOG.warning(f"[{ex.journey.get('reference')}:{step.name}] step data invalid [status:ERROR]")
        event.driver.store_step(step.name, StepStatuses.ERROR, status_info=str(ex), timestamp=event.driver.clock.timestamp)
        return InvalidDataOutcome(outcome_step=step, reason=str(ex))
