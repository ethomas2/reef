import random
import math
import time
import typing as t

import utils
import _typesv1 as types

G = t.TypeVar("G")
A = t.TypeVar("A")


def mcts_v1(config: types.MctsConfig[G, A]) -> A:
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
        leaf_node = tree_policy(config, root, tree)
        new_node = expand(config, tree, leaf_node)
        result, terminal_node = rollout_policy(config, new_node, tree)
        backup(terminal_node, result)

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
) -> types.Node[A]:
    nodes, edges = tree.nodes, tree.edges

    node = root
    while node.num_expanded == node.num_could_be_expanded:
        child_nodes = [nodes[child_id] for (child_id, _) in edges[node.id]]
        node = max(child_nodes, key=lambda node: ucb(tree, node))
    return node


def ucb(tree: types.Tree, node: types.Node) -> float:
    xj = node.value / node.times_visited
    parent = tree.nodes[node.parent_id]
    explore_term = math.sqrt(
        2 * math.log(node.times_visited) / float(parent.times_visited)
    )
    return xj + explore_term


def expand(
    config: types.MctsConfig[G, A],
    tree: types.Tree,
    node: types.Node,
    gamestate: G,
):
    pass
    # # TODO: maybe store full set of actions on the node or the tree so you
    # # don't have to call get_all_actions every time.
    # # TODO: Also instead of storing node_id_to_gamestate, consider walking back
    # # up to the root and replaying take_action_mut until you get to this node
    # take_action_mut, undo_action, get_all_actions = (
    #     config.take_action_mut,
    #     config.undo_action,
    #     config.get_all_actions,
    # )

    # used_actions = set([a for (nodeid, a) in tree.edges[node.id]])
    # all_actions = get_all_actions(gamestate)
    # unused_actions = [a for a in all_actions if a not in used_actions]
    # action = random.choice(unused_actions)
    # newgamestate = take_action_mut(gamestate, action)
    # newactions = get_all_actions(newgamestate)
    # newnode = types.Node(
    #     # TODO: make random id so you don't get conflicts with other processes
    #     id=len(tree.nodes),
    #     times_visited=0,
    #     value=0,
    #     parent_id=node.id,
    #     num_expanded=0,
    #     num_could_be_expanded=len(newactions),  # actions
    # )
    # tree.nodes[newnode.id] = newnode
    # tree.edges.setdefault(newnode.parent_id, [])
    # tree.edges[newnode.parent_id].append(newnode)
    # undo_action(newgamestate, action)
    # return newnode


def rollout_policy(
    config: types.MctsConfig[G, A],
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    gamestate: G,
) -> t.Tuple[int, terminal_node]:
    pass
    # TODO: add decisive move heuristic
    # TODO: use heuristic
    # while (result := config.is_over(gamestate)) is None:
    #     action = random.choice(config.get_all_actions(gamestate))
    #     config.take_action_mut(gamestate, action)
    # assert type(result)_== type(gamestate.turn)
    # return int(result == gamestate.turn)


def backup(terminal_node: Node, result: float):
    node = terminal_node
    while node is not None:
        terminal_node.times_visited += 1
        terminal_node.value += result
        node = tree.get(node.parent_id)
