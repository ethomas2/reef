import math
from dataclasses import dataclass
import typing as t


G = t.TypeVar("G")  # Gamestate
A = t.TypeVar("A")  # Action
P = t.TypeVar("P")  # Player

NodeId = int


# A node is not 1:1 with gamestate. A node is a series of actions from the
# root. So two nodes can have the same gamestates if the sequence of actions to
# the two nodes lead to the same gamestate
@dataclass
class Node(t.Generic[A]):
    id: NodeId
    parent_id: t.Optional[NodeId]

    times_visited: int
    value: float  # times_won

    num_children_visited: int
    num_children: int

    # @property
    # def is_expanded(self) -> bool:
    #     return self.num_expanded > 0

    # def is_fully_expanded(self) -> bool:
    #     return self.num_expanded == self.num_children


@dataclass
class Tree(t.Generic[G, A]):
    nodes: t.Dict[NodeId, Node[A]]  # node id -> node
    # parent node id -> (child node id, action it took to get to this child)
    edges: t.Dict[
        NodeId, t.List[t.Tuple[NodeId, A]]
    ]  # TODO: action could go in node.parent instead of the tree?
    # node_id_to_gamestate: t.Dict[
    #     NodeId, G
    # ]  # TODO: maybe sholdn't be part of tree


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
