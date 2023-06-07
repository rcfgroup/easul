import datetime as dt
import json

import msgpack
import numpy as np
import logging
LOG = logging.getLogger(__name__)

def decode_complex_data(obj):
    """
    Decoder which converts JSON structures into Python objects.
    Supports dates, times and time structures.

    Args:
        obj:

    Returns:

    """
    if isinstance(obj, str):
        return None

    if '__datetime__' in obj:
        return dt.datetime.fromisoformat(obj["as_str"])

    if '__date__' in obj:
        return dt.date.fromisoformat(obj["as_str"])

    if '__time__' in obj:
        return dt.time.fromisoformat(obj["as_str"])

    return None


def encode_complex_data(obj):
    """
    Encoder which converts complex objects into JSON structures.
    Supports dates, times and datetimes as well as numpy-based arrays and values.

    Args:
        obj:

    Returns:

    """
    if isinstance(obj, dt.datetime):
        return {'__datetime__': True, 'as_str': obj.isoformat()}

    if isinstance(obj, dt.date):
        return {'__date__': True, 'as_str': obj.isoformat()}

    if isinstance(obj, dt.time):
        return {'__time__': True, 'as_str': obj.isoformat()}

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if issubclass(obj.__class__, np.generic) is True:
        return obj.item()

    return None


class NpEncoder(json.JSONEncoder):
    """
    Encoder class for Python 'json' library.
    """
    def default(self, obj):
        encoded = encode_complex_data(obj)
        if encoded is not None:
            return encoded

        return super().default(obj)


class NpDecoder(json.JSONDecoder):
    """
    Decoder class for Python 'json' library.
    """
    def decode(self, s):
        decoded = decode_complex_data(s)
        if decoded is not None:
            return decoded

        return super().decode(s)


class JsonCodec:
    """
    Codec to convert from/to JSON from/to Python structures.
    """
    @classmethod
    def encode(cls, data):
        return json.dumps(data, cls=NpEncoder)

    @classmethod
    def decode(cls, value):
        return json.loads(value, cls=NpDecoder)


class MsgPack:
    """
    Codec to convert from/to JSON from/to MsgPack structures.
    """

    DATE_FORMAT = "%Y-%m-%d"

    @staticmethod
    def _decode_datetime(obj):
        if '__datetime__' in obj:
            return dt.datetime.fromisoformat(obj["as_str"])

        if '__date__' in obj:
            return dt.date.fromisoformat(obj["as_str"])

        if '__time__' in obj:
            return dt.time.fromisoformat(obj["as_str"])

        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    @staticmethod
    def _encode_datetime(obj):
        if isinstance(obj, dt.datetime):
            return {'__datetime__': True, 'as_str': obj.isoformat()}

        if isinstance(obj, dt.date):
            return {'__date__': True, 'as_str': obj.isoformat()}

        if isinstance(obj, dt.time):
            return {'__time__': True, 'as_str': obj.isoformat()}

        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return obj

    @classmethod
    def encode(cls, data):
        return msgpack.packb(data, default=cls._encode_datetime)

    @classmethod
    def decode(cls, value):
        if value is None:
            return None

        return msgpack.unpackb(value, object_hook=cls._decode_datetime)