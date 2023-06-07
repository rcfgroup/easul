import logging

from easul.outcome import PauseOutcome
LOG = logging.getLogger(__name__)
from easul.util import is_successful_outcome

def run_step_chain(next_step, driver, previous_outcome=None):
    """
    Run the chain of steps iterative which start at next_step.
    Args:
        next_step:
        driver:
        previous_outcome:

    Returns:

    """
    outcome = next_step.run_all(driver, previous_outcome=previous_outcome)
    if not outcome:
        LOG.info(f"[{driver.journey.get('reference')}:END] - no outcome")
        return

    if not outcome.next_step:
        if is_successful_outcome(outcome) and driver.journey.get("complete") != 1:
            LOG.error(
                f"Journey '{driver.journey.get('reference')}' is not marked complete, but no next step was obtained from latest step {next_step}")
        return

    if isinstance(outcome, PauseOutcome):
        return

    run_step_chain(outcome.next_step, driver, previous_outcome = outcome)
