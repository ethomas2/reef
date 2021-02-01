import math
from dataclasses import dataclass
import typing as t


G = t.TypeVar("G")  # Gamestate
A = t.TypeVar("A")  # Action
P = t.TypeVar("P")  # Player

NodeId = int


class HeuristicVal(t.NamedTuple):
    numerator: float
    denominator: int


# A node is not 1:1 with gamestate. A node is a series of actions from the
# root. So two nodes can have the same gamestates if the sequence of actions to
# the two nodes lead to the same gamestate
@dataclass
class Node(t.Generic[A]):
    id: NodeId
    parent_id: t.Optional[NodeId]

    times_visited: int
    wins_vec: t.Dict[
        P, int
    ]  # map from player to how many times this player has won

    player: P  # whose turn it is to move

    heuristic_val: t.Optional[HeuristicVal] = None


@dataclass
class Tree(t.Generic[G, A]):
    nodes: t.Dict[NodeId, Node[A]]  # node id -> node

    edges: t.Dict[
        NodeId, t.List[t.Tuple[NodeId, A]]
    ]  # TODO: action could go in node.parent instead of the tree?


@dataclass
class MutableActionConfig(t.Generic[G, A]):
    take_action_mut: t.Callable[[G, A], t.Optional[G]]
    undo_action: t.Callable[[G, A], t.Optional[G]]


@dataclass
class ImmutableActionConfig(t.Generic[G, A]):
    take_action_immut: t.Callable[[G, A], t.Optional[G]]


@dataclass
class MctsConfig(t.Generic[G, A]):
    take_action_mut: t.Callable[[G, A], t.Optional[G]]
    undo_action: t.Callable[[G, A], t.Optional[G]]
    get_all_actions: t.Callable[[G], t.Iterable[A]]
    is_over: t.Callable[[G], t.Optional[int]]
    players: t.List[P]

    heuristic_type: t.Optional[str] = None
    heuristic: t.Optional[t.Callable[[G], float]] = None
    C = 1 / math.sqrt(2)

    # TODO: change budget to terminationconfig, allows time bank or thing where
    # final node has to be same as something
    budget: float = 1.0
    decisive_moves_heuristic: bool = False
    decisive_moves_heuristic_with_propogation: bool = False


@dataclass
class MinimaxConfig(t.Generic[G, A, P]):
    action: t.Union[MutableActionConfig[G, A], ImmutableActionConfig[G, A]]
    get_all_actions: t.Callable[[G], t.Iterable[A]]
    is_over: t.Callable[[G], t.Optional[P]]
    heuristic: t.Callable[[G], float]
    get_player: t.Callable[[G], P]
    other_player: t.Callable[[P], P]
