import typing as t
from dataclasses import dataclass


"""
Messages sent to and from redis
"""


GameType = t.Union[
    t.Literal["2048"],
    t.Literal["connect4"],
]


@dataclass
class NewGamestate:
    command_type: t.Literal["new-gamestate"]
    game_type: GameType
    gamestate_id: int
    gamestate: bytes  # encoded gamestate


@dataclass
class NewConfig:
    command_type = t.Literal["new-config"]
    game_type: GameType


@dataclass
class Stop:
    pass
