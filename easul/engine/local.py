from easul import DataFrameSource
from easul.engine import Engine
from easul.engine.memory import MemoryBroker, MemoryClient
from easul.driver import HourlyClock

from datetime import timedelta as td
import logging
LOG = logging.getLogger(__name__)

class LocalEngine(Engine):
    """
    Local engine which will run a specific
    """
    broker = MemoryBroker()
    client = MemoryClient()

    def __init__(self, sources, reference_name, start_ts_field, end_ts_field, timespan=None):
        self.sources = sources
        self.reference_data = sources[reference_name]
        self.reference_field = sources[reference_name].reference_field
        self.start_ts_field = start_ts_field
        self.end_ts_field = end_ts_field

    def new_clock(self, start_ts, end_ts, **kwargs):
        return HourlyClock(start_ts=start_ts, end_ts=end_ts)

    def run(self, plan):
        from easul.util import copy_plan_with_new_sources
        plan_copy = copy_plan_with_new_sources(plan, self.sources)

        reference_field = self.reference_field
        reference_data = self.reference_data

        for idx, adm in enumerate(reference_data):
            start_ts = adm[self.start_ts_field]
            end_ts = adm[self.end_ts_field]

            journey = self.client.get_journey(reference=adm[reference_field], source="admissions")

            if not journey:
                journey = self.client.create_journey(reference=adm[reference_field], source="admissions")

            clock = self.new_clock(start_ts, end_ts)
            driver = self.new_driver(journey=journey, clock=clock)

            n = 0

            while (clock.has_ended() is False):
                if n % 24 == 0:
                    LOG.info(f"**** DAY {n} ({clock.timestamp}) {driver.journey['reference']}")

                plan_copy.run(driver)

                if "complete" in driver.journey and driver.journey["complete"] == 1:
                    break

                clock.advance()
                n += 1

            if "complete" in driver.journey and driver.journey["complete"] != 1:
                LOG.info(f"journey {driver.journey['reference']} complete")
                self.client.complete_journey(driver.journey_id)

        LOG.info(f"{idx+1} journeys complete")


    def new_empty_driver(self, is_empty=False, clock=None):
        from easul.driver import EmptyDriver

        return EmptyDriver(client=self.client, broker=self.broker, clock=clock)

    def new_driver(self, reference=None, source=None, journey=None, clock=None):
        from easul.driver import Driver

        if journey:
            return Driver.from_journey(journey=journey, client=self.client, broker=self.broker, clock=clock)

        return Driver.from_reference(reference=reference, source=source, client=self.client,
                              broker=self.broker, clock=clock)

    def get_outcomes(self):
        journeys = self.client.get_journeys()
        states = []
        steps = []
        for journey in journeys:
            states.extend([dict(**j, **{"reference": journey["reference"]}) for j in journey["states"]])
            steps.extend([dict(**j, **{"reference": journey["reference"]}) for j in journey["steps"]])

        return states, steps




