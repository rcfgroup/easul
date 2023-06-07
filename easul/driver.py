import logging

from easul.engine.memory import MemoryClient, MemoryBroker
from easul.util import is_successful_outcome

LOG = logging.getLogger(__name__)
import datetime as dt

class Clock:
    """
    Base Clock which supports temporal situations.
    """
    timestamp = None

class LocalClock(Clock):
    """
    Clock which returns the current local time as the timestamp
    """
    def __init__(self, engine=None):
        self.engine = None

    @property
    def timestamp(self):
        return dt.datetime.now()

    def __call__(self, engine):
        return LocalClock(engine)

class HourlyClock(Clock):
    """
    Clock which has defined start and end, and increments by an hour when advanced.
    """
    def __init__(self, start_ts, end_ts):
        secs = 3600
        start_ts_unix = int((start_ts.timestamp() / secs) - 1) * secs
        start_ts = dt.datetime.fromtimestamp(start_ts_unix)

        end_ts_unix = int((end_ts.timestamp() / secs) + 1) * secs
        end_ts = dt.datetime.fromtimestamp(end_ts_unix)

        self.start_ts = start_ts
        self.end_ts = end_ts
        self.timestamp = self.start_ts
        self.increment_by = dt.timedelta(seconds=secs)

    def advance(self):
        self.timestamp+=self.increment_by

    def has_ended(self):
        if self.timestamp>self.end_ts:
            return True

        return False

class Driver:
    """
    Provides a wrapper for methods from both the broker and the client to help 'drive' the
    journey. The clock provides temporal support and indicates timestamps used in persistence etc.
    """
    def __init__(self, journey, client, broker, clock):
        self._client = client
        self._broker = broker
        self.journey_id = journey["id"]
        self.journey = journey
        self.clock = clock

    @classmethod
    def from_reference(cls, reference, source, client, broker, label=None, clock=None):
        """
        Create Driver based on journey obtained from client according to reference.
        Args:
            reference:
            source:
            client:
            broker:
            label:
            clock:

        Returns:

        """
        journey = client.get_journey(reference=reference, source=source)

        if not journey:
            raise ValueError(f"No journey with reference '{reference}'")

        return Driver(journey=journey, client=client, broker=broker, clock=clock)

    @classmethod
    def from_journey(cls, journey, client, broker, clock=None):
        """
        Create Driver based on journey previously obtained.
        Args:
            journey:
            client:
            broker:
            clock:

        Returns:

        """
        if type(journey) is not dict:
            journey = vars(journey)

        return Driver(journey, client, broker, clock=clock)

    def store_state(self, state_label, state, from_step, reason=None):
        """
        Store current state in client.
        Args:
            state_label:
            state:
            from_step:
            reason:

        Returns:

        """
        self._client.set_current_state(state_label, state, journey_id=self.journey_id, reason=reason, from_step=from_step, timestamp=self.clock.timestamp)

    def store_step(self, step_name, status, status_info=None, outcome=None, timestamp=None):
        """
        Store step status and other info in client.
        Args:
            step_name:
            status:
            status_info:
            outcome:
            timestamp:

        Returns:

        """
        self._client.set_current_step(step_name, status=status.name, status_info=status_info, journey_id=self.journey_id,
                                      outcome=outcome.asdict() if is_successful_outcome(outcome) else None, timestamp=timestamp)

    @property
    def current_states(self):
        """
        Get current states from client.

        Returns:

        """
        return self._client.get_current_states(journey_id=self.journey_id)

    @property
    def all_states(self):
        """
        Get all states from client (including historical states)

        Returns:

        """
        return self._client.get_all_states(journey_id=self.journey_id)

    def get_current_journey_step(self):
        """
        Get current step in journey from client.

        Returns:

        """
        latest_step = self._client.get_latest_step(journey_id=self.journey_id)

        if not latest_step:
            return None

        return latest_step

    def get_specific_step(self, step_name):
        """
        Get specific step from client for journey.

        Args:
            step_name:

        Returns:

        """
        specific_step = self._client.get_step(step_name=step_name, journey_id=self.journey_id)

        if not specific_step:
            return None

        return specific_step


    def get_route(self):
        """
        Get list of step names which have been followed by the patient in this journey.
        Returns:

        """
        return self._client.get_step_route(journey_id=self.journey_id)

    def get_broker_data(self, data_type):
        """
        Get specific data from the broker for this journey.
        Args:
            data_type:

        Returns:

        """
        bdata = self._broker.retrieve_data(self.journey["reference"], data_type)
        if not bdata:
            return None

        return bdata


    def store_data_in_broker(self, *args, **kwargs):
        """
        Store data in the broker
        Args:
            *args: 
            **kwargs: 

        Returns:

        """
        return self._broker.store_data(*args, **kwargs)

    def send_broker_message(self, reference, data_type, data, external=False):
        """
        Send a message to the broker.
        Args:
            reference: 
            data_type: 
            data: 
            external: 

        Returns:

        """
        from easul.engine import Channels

        channel_name = Channels.EXTERNAL if external else Channels.INTERNAL
        full_data = {"reference": reference, "data_type": data_type, "data": data}

        self._broker.send_message(channel_name, full_data)

    def __repr__(self):
        return f"<Driver journey_id={self.journey_id}, client={self._client}, broker={self._broker}>"


class MemoryDriver(Driver):
    """
    A Driver which handles everything as data structures in memory including client and broker data.
    This is useful for simulation and testing as it does not require external services, but it will not scale for
    distributed or large-scale analytics.
    """
    @staticmethod
    def from_reference(reference, autocreate=False, source="memory", clock=None):
        client = MemoryClient()
        if autocreate:
            journey = client.get_journey(reference=reference, source=source)
            if not journey:
                client.create_journey(reference=reference, source=source)

        return Driver.from_reference(reference=reference, source=source, client=client, broker=MemoryBroker(), label=None, clock=clock)


class EmptyDriver(Driver):
    """
        Provides a wrapper for methods from both the broker and the client to help 'drive' the
        journey.
        """

    def __init__(self, client, broker, clock):
        self._client = client
        self._broker = broker
        self.journey_id = None
        self.journey = None
        self.clock = clock

    def get_route(self):
        return []