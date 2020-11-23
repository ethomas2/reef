from dataclasses import dataclass
import typing as t

XSpace = t.Literal["X"]
OSpace = t.Literal["O"]
Marking = t.Union[XSpace, OSpace]

Space = t.Optional[Marking]

Board = t.List[t.List[Space]]


@dataclass
class GameState:
    board: Board
    num_moves: int
    turn: Marking


Action = t.Tuple[int, Marking]
