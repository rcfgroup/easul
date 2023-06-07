import logging
from abc import abstractmethod
from datetime import datetime as dt, timedelta as td

from easul.util import create_package_class

import logging
from easul.error import StepDataNotAvailable
from easul.driver import Driver
logging.basicConfig(level=logging.INFO)

LOG = logging.getLogger(__name__)

class JourneyCallback:
    """
    Callback for execution of single journey used by the engine.
    """
    def __init__(self, plan, engine):
        self.plan = plan
        self.client = engine.client
        self.clock = engine.clock
        self.engine = engine

    def __call__(self, params, broker):
        reference = params.get("reference")
        data_type = params.get("data_type")

        if data_type in self.plan.config.get("watch_messages",[]):
            start_step = data_type
        else:
            start_step = None

        journey = self.client.get_journey(reference=reference)

        if not journey:

            LOG.info(f"Create journey (not found): {reference}")
            journey = self.client.create_journey(reference=reference, label="", source="")

        itin = Driver.from_journey(journey=journey, client=self.client, broker=broker, clock=self.clock(self.engine))

        try:
            if start_step:
                self.plan.run_from(start_step, itin)
            else:
                self.plan.run(itin)
        except StepDataNotAvailable as ex:
            self.handle_data_not_available(ex)

    def handle_data_not_available(self, ex):
        LOG.warning(f"[{ex.journey.get('reference')}:{ex.step_name}] Data not available" + (
            f" REATTEMPT ({ ex.delay }s delay)" if ex.retry else ""))
