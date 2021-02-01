import dataclasses
import math
import typing as t


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
