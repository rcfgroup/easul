from abc import abstractmethod

import logging

from easul.engine.codec import JsonCodec


LOG = logging.getLogger(__name__)

class ClientError(BaseException):
    def __init__(self, url, data, status_code):
        super().__init__(f"Client error from URL:{url}, error:{data} - status:{status_code}")

class Client:
    """
    Base Client class
    """
    @abstractmethod
    def create_journey(self, reference, source, label=None):
        pass

    @abstractmethod
    def get_journey(self, id=None, reference=None, source=None):
        pass

    @abstractmethod
    def set_current_state(self, state_label, state, journey_id=None, reference=None, reason=None, from_step=None, timestamp=None):
        pass

    @abstractmethod
    def set_current_step(self, step_name, status, status_info=None, journey_id=None, reference=None, outcome=None, complete=False):
        pass

    @abstractmethod
    def get_current_state(self, state_label, journey_id=None, reference=None):
        pass

    @abstractmethod
    def get_current_states(self, journey_id=None, reference=None):
        pass

    @abstractmethod
    def get_all_states(self, journey_id=None, reference=None):
        pass

    @abstractmethod
    def get_latest_step(self, journey_id=None, reference=None):
        pass

    @abstractmethod
    def get_step(self, step_name, journey_id=None, reference=None):
        pass

    @abstractmethod
    def get_step_route(self, journey_id):
        pass

    @abstractmethod
    def get_journeys(self):
        pass

    @abstractmethod
    def complete_journey(self, journey_id=None, reference=None):
        pass
#
# @dataclass
# class BrokerData:
#     reference:str
#     data_type:str
#     data:Dict[str,Any]


class Broker:
    """
    Base Broker client
    """
    codec = JsonCodec

    def decode_message(self, message):
        if type(message) is dict and message["type"] == "message":
            message = message["data"]

        if message is None:
            return None

        decoded = self.codec.decode(message)
        return decoded

    def encode_data(self, data):
        return self.codec.encode(data)

    def store_data(self, reference, data_type, data, external=False):
        pass

    def retrieve_data(self, reference, data_type):
        pass


class Channels:
    """
    Enum for Channels types
    """
    INTERNAL = "internal"
    EXTERNAL = "external"

class Engine:
    """
    Base Engine class
    """
    broker = None
    client = None

    @classmethod
    def run(cls, plan):
        pass

    @classmethod
    def new_empty_driver(cls, is_empty=False, clock=None):
        from easul.driver import EmptyDriver

        return EmptyDriver(client=cls.client, broker=cls.broker, clock=clock)

    @classmethod
    def new_driver(cls, reference, source=None):
        from easul.driver import Driver

        return Driver.from_reference(reference=reference, source=source, client=cls.client,
                              broker=cls.broker, clock=cls.clock)


