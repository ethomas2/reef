import contextlib
import random
import math
import time
import typing as t

import _typesv1 as types

G = t.TypeVar("G")
A = t.TypeVar("A")


def mcts_v1(config: types.MctsConfig[G, A], gamestate: G) -> A:
    start = time.time()
    end = start + config.budget
    root = types.Node(
        id=0,
        parent=None,
        times_visited=0,
        value=0,
        terminal=None,
    )
    tree = types.Tree(nodes=[], edges={}, node_id_to_gamestate={})

    while time.time() < end:
        leaf_node = tree_policy(config, root, tree, gamestate)
        new_node = expand(config, tree, leaf_node, gamestate)
        result = rollout_policy(config, new_node, tree, gamestate)
        backup(config, tree, new_node, result)

    child_action_pairs = (
        (tree.nodes[child_id], action)
        for (child_id, action) in tree.edges[root.id]
    )
    action_value_pairs = [
        (action, child.value / float(child.times_visited))
        for (child, action) in child_action_pairs
    ]

    action, _ = max(action_value_pairs, key=lambda x: x[1])
    return action


def tree_policy(
    config: types.MctsConfig[G, A],
    root: types.Node[A],
    tree: types.Tree[G, A],
    gamestate: G,
) -> (types.Node[A], bool):
    nodes, edges = tree.nodes, tree.edges

    node = root
    # assert edges.get(node.id) is not None
    while True:
        is_not_expanded = edges.get(node.id) is None
        if is_not_expanded:
            return node

        child_nodes = [nodes[child_id] for (child_id, _) in edges[node.id]]
        is_fully_expanded = all(
            child.times_visited > 0 for child in child_nodes
        )
        is_terminal = child_nodes == []
        if not is_fully_expanded or is_terminal:
            break
        node = max(child_nodes, key=lambda node: ucb(config, tree, node))
    assert _is_leaf(node)
    return node


def _is_leaf(node):
    """
    Return if this node has a child that
    """
    return False


def ucb(config: types.MctsConfig, tree: types.Tree, node: types.Node) -> float:
    xj = node.value / node.times_visited
    parent = tree.nodes[node.parent_id]
    explore_term = config.C * math.sqrt(
        math.log(node.times_visited) / float(parent.times_visited)
    )
    return xj + explore_term


def expand(
    config: types.MctsConfig[G, A],
    tree: types.Tree,
    node: types.Node,
    gamestate: G,
):
    """
    Expand a node.

    To expand a node is to
    1. Add all it's children to the tree (if they're not already)
    2. Run a simulation from one of it's children that has not been visited

    Fully expanded: A node for whom all children have had a simulation run
    """
    nodes, edges = tree.nodes, tree.edges

    child_action_pairs = edges.get(node.id)
    if not child_action_pairs:
        add_children_to_tree(config, tree, node, gamestate)

    child_nodes = (nodes[child_id] for (child_id, _) in edges[node.id])
    unvisited_children = [
        node for node in child_nodes if node.times_visited == 0
    ]
    arbitrary_unvisited_child = random.choices(unvisited_children)
    return arbitrary_unvisited_child


def add_children_to_tree(
    config: types.MctsConfig[G, A],
    tree: types.Tree,
    node: types.Node,
    gamestate: G,
):
    """
    Add all children of `node` to the tree. Node must not have any children in
    the tree yet.
    """

    assert tree.edges.get(node.id) is None or tree.edges[node.id] == []
    tree.edges[node.id] = []
    for action in config.get_all_actions(gamestate):
        child_node = types.Node(
            id=random.getrandbits(64),
            parent_id=node.id,
            times_visited=0,
            value=0,
            num_children_visited=0,
            num_children=None,
        )

        tree.nodes[child_node.id] = child_node
        tree.edges[node.id].append((child_node, action))


def rollout_policy(
    config: types.MctsConfig[G, A],
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    gamestate: G,
) -> int:
    # TODO: add decisive move heuristic
    # TODO: use heuristic
    while (result := config.is_over(gamestate)) is None:
        action = random.choice(config.get_all_actions(gamestate))
        config.take_action_mut(gamestate, action)
    assert type(result) == type(gamestate.turn)
    return int(result == gamestate.turn)


def backup(
    config: types.MctsConfig,
    tree: types.Tree[G, A],
    node: types.Node,
    result: float,
):
    while node is not None:
        node.times_visited += 1
        node.value += result
        node = tree.get(node.parent_id)


# @contextlib
# def action_guard(config: types.MctsConfig, gamestate: G):
# actions = []
# def take_action_mut_with_log(gamestate: G, action: A) -> t.Optional[G]:
#     actions.append(action)
#     return config.take_action_mt(gamestate, action)

# yield take_action_mut_with_counter

# for action in reversed(actions_taken):
#     gamestate = config.undo_action(gamestate, action)
