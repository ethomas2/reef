import time
import typing as t

import utils
import _typesv1 as types

G = t.TypeVar("G")
A = t.TypeVar("A")


def mcts_v1(config: types.MctsConfig[G, A]) -> A:
    start = time.time()
    end = start + config.budget
    root = types.Node[A](
        id=0,
        parent=None,
        times_visited=0,
        times_won=0,
        terminal=None,
    )
    tree = types.Tree[G, A](nodes=[], edges={}, node_id_to_gamestate={})
    next_id = 1

    while time.time() < end:
        leaf_node = tree_policy(config, root, tree)
        result, terminal_node = rollout_policy(config, leaf_node, tree)
        backup(terminal_node, result)

    children = tree[root.id]
    bestchild = max(
        children,
        key=lambda child: float(child.times_visited) / child.times_won,
    )

    parent = bestchild.parent
    if parent is None:
        utils.assert_never("best child has no parent")
    _, act = parent
    return act


def expand(node: types.Node):
    pass
    # child_nodes = [
    #     types.Node(
    #         id=next_id + i,
    #         parent=root.id,
    #         times_visited=0,
    #         times_won=0,
    #         terminal=is_over(child_state),
    #     )
    #     for i, (child_state, action) in enumerate(get_child_states())
    # ]


def child_states(gs: G):
    if undo_action is not None:
        for act in get_all_actions(gs):
            new_gs = take_action_mut(gs, act)
            yield new_gs, act
            gs = undo_action(new_gs, act)
    else:
        raise NotImplementedError


def tree_policy(
    config: types.MctsConfig[G, A],
    root: types.Node[A],
    tree: types.Tree[G, A],
):
    nodes, edges, node_id_to_gamestate = (
        tree.nodes,
        tree.edges,
        tree.node_id_to_gamestate,
    )

    node = root
    while node.terminal is None:
        children = edges.get(node.id)
        if children is not None:
            # node isn't terminal, so the fact that it has no children means
            # it's not expanded
            return expand(node)
        else:
            node = bestchild(node)


def expand(node: types.Node[A]):
    pass


def rollout_policy(
    config: types.MctsConfig[G, A],
    root: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
) -> t.Tuple[int, terminal_node]:
    pass


def mcts_v2():
    """
    Red blue strategy (blue nodes are random)
    """
    pass


def mcts_v3():
    """
    Red blue strategy with parallelization
    """
    pass
