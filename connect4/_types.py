from dataclasses import dataclass
import typing as t

XSpace = t.Literal["X"]
OSpace = t.Literal["O"]
Player = t.Union[XSpace, OSpace]

Space = t.Optional[Player]

Board = t.List[t.List[Space]]


@dataclass
class GameState:
    board: Board
    num_moves: int
    turn: Player


Action = t.Tuple[int, Player]
