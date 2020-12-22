import math
from dataclasses import dataclass
import typing as t


G = t.TypeVar("G")  # Gamestate
A = t.TypeVar("A")  # Action
P = t.TypeVar("P")  # Player


@dataclass
class Node(t.Generic[A]):
    id: int
    # The parent id and action it took to get from parent to here
    parent: t.Optional[t.Tuple[int, A]]
    times_visited: int
    times_won: int

    # None for non-terminal, -1, 0, 1 for
    terminal: t.Optional[int]


@dataclass
class Tree(t.Generic[G, A]):
    nodes: t.List[Node[A]]
    edges: t.Dict[int, t.List[int]]
    node_id_to_gamestate: t.Dict[int, G]


@dataclass
class MutableActionConfig(t.Generic[G, A]):
    take_action_mut: t.Callable[[G, A], t.Optional[G]]
    undo_action: t.Callable[[G, A], t.Optional[G]]


@dataclass
class ImmutableActionConfig(t.Generic[G, A]):
    take_action_immut: t.Callable[[G, A], t.Optional[G]]


@dataclass
class MctsConfig(t.Generic[G, A]):
    gamestate: G
    action: t.Union[MutableActionConfig[G, A], ImmutableActionConfig[G, A]]
    get_all_actions: t.Callable[[G], t.Iterable[A]]
    is_over: t.Callable[[G], t.Optional[int]]

    heuristic: t.Optional[t.Callable[[G], float]] = None
    C = 1 / math.sqrt(2)

    # TODO: change budget to terminationconfig, allows time bank or thing where
    # final node has to be same as something
    budget: float = 1.0
    decisive_moves_heuristic: bool = False


@dataclass
class MinimaxConfig(t.Generic[G, A, P]):
    action: t.Union[MutableActionConfig[G, A], ImmutableActionConfig[G, A]]
    get_all_actions: t.Callable[[G], t.Iterable[A]]
    is_over: t.Callable[[G], t.Optional[P]]
    heuristic: t.Callable[[G], float]
    get_player: t.Callable[[G], P]
    other_player: t.Callable[[P], P]
