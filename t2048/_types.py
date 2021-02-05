from dataclasses import dataclass
import typing as t

Board = t.List[t.List[t.Optional[int]]]

Player = t.Union[t.Literal["player"], t.Literal["environment"]]


@dataclass
class GameState:
    player: Player
    board: Board


@dataclass
class PlayerAction:
    action: t.Union[
        t.Literal["up"],
        t.Literal["down"],
        t.Literal["left"],
        t.Literal["right"],
    ]


@dataclass
class EnvironmentAction:
    placement: t.Tuple[int, int]
    val: int


Action = t.Union[PlayerAction, EnvironmentAction]
