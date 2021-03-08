import time
import importlib
import dataclasses
import json
import math
import sys
import typing as t

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
        return deserialize(
            pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=timeout,
            )
        )
    else:
        while True:
            msg = pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=10,
            )
            if msg is not None:
                data = json.loads(msg["data"])
                klass = getattr(
                    importlib.import_module(data["dc_module"]), data["dc_name"]
                )
                return klass(
                    **{
                        k: v
                        for k, v in data.items()
                        if k not in ["dc_module", "dc_name"]
                    }
                )


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


def write_chan(r: redis.Redis, channel: str, dc):
    r.publish(channel, serialize(dc))


def serialize(dc):
    d = dc.__dict__
    d["dc_module"] = type(dc).__module__
    d["dc_name"] = type(dc).__name__
    return json.dumps(d)


def deserialize(msg):
    if msg is None:
        return None
    data = json.loads(msg["data"])
    klass = getattr(
        importlib.import_module(data["dc_module"]), data["dc_name"]
    )
    return klass(
        **{k: v for k, v in data.items() if k not in ["dc_module", "dc_name"]}
    )
