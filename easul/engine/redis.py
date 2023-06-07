import redis

from easul.engine import Broker, Channels
from easul.engine.codec import MsgPack
import logging

LOG = logging.getLogger(__name__)

class RedisBroker(Broker):
    """
    Broker which uses Redis as its basis.
    """
    codec = MsgPack

    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)


    def new_pubsub(self, *args, **kwargs):
        return self.client.pubsub(*args, **kwargs)


    def create_channel(self, channel_name, channel_callback=None):
        pubsub = self.client.pubsub(ignore_subscribe_messages=True)

        if channel_callback:
            pubsub.subscribe(**{channel_name: self._channel_wrapper(channel_callback)})
        else:
            pubsub.subscribe(channel_name)

        return pubsub


    def _channel_wrapper(self, channel_callback):
        def _internal(msg):
            if not msg:
                return None

            msg = self.decode_message(msg)

            return channel_callback(msg, self)

        return _internal

    def store_data(self, reference, data_type, data, external=False, send_message=False):

        with self.client.pipeline() as p:
            p.set(data_type + ":" + reference, self.encode_data(data))

            if send_message:
                if external:

                    p.publish(Channels.EXTERNAL, self.codec.encode({"reference":reference, "data_type":data_type, "data":data}))
                else:
                    p.publish(Channels.INTERNAL, self.codec.encode({"reference":reference}))

            p.execute()

    def retrieve_data(self, reference, data_type):
        msg = self.client.get(data_type + ":" + reference)
        data = self.decode_message(msg)
        if not data:
            return

        return data

