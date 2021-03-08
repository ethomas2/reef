import dataclasses
import importlib
import json
import math
import sys
import time
import typing as t
import utils

import redis.client


def assert_never(msg: str) -> t.NoReturn:
    raise Exception(msg)


T = t.TypeVar("T")


def get_and_validate_input(
    msg: str, validate: t.Callable[[str], t.Any]
) -> str:
    while True:
        inp = input(msg)
        try:
            if not validate(inp):
                continue
            return inp
        except Exception:
            continue


def get_and_transform_input(msg: str, transform: t.Callable[[str], T]) -> T:
    while True:
        inp = input(msg)
        try:
            return transform(inp)
        except Exception:
            continue


def copy(obj):
    """
    A faster version of copy.deepcopy for dataclasses

    Using copy.deepcopy on types.Gamestate takes about 2ms
    Using this method on types.Gamestate takes about 1.9 ms
    """
    if dataclasses.is_dataclass(obj):
        Class = type(obj)
        return Class(
            **{
                f.name: copy(getattr(obj, f.name))
                for f in dataclasses.fields(obj)
            }
        )
    elif isinstance(obj, list):
        return [copy(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: copy(v) for k, v in obj.items()}
    else:
        return obj


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def print_err(msg, exit=False):
    print(f"\033[31m{msg}\033[m")
    if exit:
        sys.exit(1)


#################################### Redis ####################################


def read_chan(pubsub: redis.client.PubSub, timeout: t.Optional[int] = None):
    """
    Filter out messages that aren't of type "message". timeout=None means block
    (wait until there's a message)

    Serialization stolen from https://stackoverflow.com/a/8790232
    """
    if timeout is not None:

        msg = pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=timeout,
        )
        if msg is None:
            return None
        return deserialize(msg["data"])
    else:
        while True:
            msg = pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=10,
            )
            if msg is not None:
                return deserialize(msg["data"])


def read_all_from_chan(pubsub: redis.client.PubSub, timeout: int):
    """
    Read from the chan from <teimout> seconds and return everything read
    """
    messages = []
    end = time.time() + timeout
    while time.time() < end:
        msg = read_chan(pubsub, max(end - time.time(), 0))
        if msg is not None:
            messages.append(msg)
    return messages


def write_chan(r: redis.Redis, channel: str, data):
    r.publish(channel, serialize(data))


def write_stream(
    stream: str, r: t.Union[redis.Redis, redis.client.Pipeline], data
):
    r.xadd(
        stream,
        {"key": serialize(data)},
    )


def read_stream(
    stream_name: str,
    r: redis.Redis,
    last_id: str,
    block: t.Optional[int] = None,
) -> t.List[t.Any]:
    result = r.xread({stream_name: last_id}, block=block)

    # result looks like this
    # [
    #   [
    #     b'stream_name', [
    #       (b'1615142762573-0', {b'key': <serialized-val>'}),
    #       (b'1615142830679-0', {b'key': <serialized-val>})]
    #   ]
    # ]
    # we're only reading from one stream, the outer array is of length 1

    ts_item_tuples = next(
        (
            stream_items
            for result_stream_name, stream_items in result
            if result_stream_name == stream_name
        ),
        None,
    )
    # ts_item_tuples looks like
    #   [(b'1615142762573-0', {b'key': <serialized-val>}),
    #    (b'1615142830679-0', {b'key': <serialized-val>})]
    if ts_item_tuples is None or ts_item_tuples == []:
        return []

    deserialized_ts_item_tuples = [
        (ts, utils.deserialize(item[b"key"])) for ts, item in ts_item_tuples
    ]
    # deserialized_ts_item_tuples looks like
    #   [(b'1615142762573-0', <deserialized>}),
    #    (b'1615142830679-0', <deserialized>)]
    return deserialized_ts_item_tuples


def serialize(_data):
    """
    Take a python value and prepare it to be written to redis. Outputs either a bytes or str
    """

    def _serialize(data):
        if isinstance(data, dict):
            return {k: _serialize(v) for (k, v) in data.items()}
        elif dataclasses.is_dataclass(data):
            d = data.__dict__
            d["dc_module"] = type(data).__module__
            d["dc_name"] = type(data).__name__
            return d
        elif isinstance(data, int):
            return data
        elif isinstance(data, str):
            return data
        elif isinstance(data, list):
            return [_serialize(x) for x in data]
        else:
            raise Exception(f"Cannot serialize datatype {type(data)}")

    return json.dumps(_serialize(_data), sort_keys=True)


def deserialize(_msg):
    """
    take _msg (bytes or str) and convert it to a python type.
    """

    def _deserialize(msg):
        if msg is None:
            return None
        elif isinstance(msg, int):
            return msg
        elif isinstance(msg, str):
            return msg
        elif isinstance(msg, list):
            return [_deserialize(x) for x in msg]
        elif isinstance(msg, dict):
            if (
                "dc_module" in msg and "dc_name" in msg
            ):  # assume it's a serialized dataclass
                klass = getattr(
                    importlib.import_module(msg["dc_module"]), msg["dc_name"]
                )
                return klass(
                    **{
                        k: v
                        for k, v in msg.items()
                        if k not in ["dc_module", "dc_name"]
                    }
                )
            else:
                return {k: _deserialize(v) for (k, v) in msg.items()}
        else:
            raise Exception(f"Cannot desriralize datatype {type(msg)}")

    if _msg is None:
        return None

    return _deserialize(json.loads(_msg))
