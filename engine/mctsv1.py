import contextlib
import random
import math
import time
import typing as t

import engine.typesv1 as types


G = t.TypeVar("G")
A = t.TypeVar("A")


def mcts_v1(config: types.MctsConfig[G, A], gamestate: G) -> A:
    start = time.time()
    end = start + config.budget
    root = types.Node(
        id=0,
        parent_id=-1,
        times_visited=0,
        value=0,
    )
    tree = types.Tree(nodes={}, edges={})

    while time.time() < end:
        with action_logger(config.take_action_mut) as (take_action_mut, log):
            leaf_node = tree_policy(
                config, root, tree, take_action_mut, gamestate
            )
            result = simulate(
                config, leaf_node, tree, take_action_mut, gamestate
            )
            backup(config, tree, leaf_node, result)
            undo_actions(gamestate, config.undo_action, log)

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
    take_action_mut: t.Callable[[G, A], t.Optional[G]],
    gamestate: G,
) -> (types.Node[A], bool):
    nodes, edges = tree.nodes, tree.edges

    node = root
    while True:
        children = edges.get(node.id)
        if children is None:
            return expand(config, tree, node, gamestate)

        if children == []:
            return node

        unvisited_child = random.choice(
            [
                nodes[child_id]
                for (child_id, _) in children
                if nodes[child_id].times_visited == 0
            ]
        )

        if unvisited_child is not None:
            return unvisited_child

        child, action = max(
            children,
            key=lambda child_id_action: ucb(
                config, tree, nodes[child_id_action[0]]
            ),
        )


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
    nodes, edges = tree.nodes, tree.edges

    child_action_pairs = edges.get(node.id)
    assert not child_action_pairs
    if not child_action_pairs:
        add_children_to_tree(config, tree, node, gamestate)

    if type(node.id) != type(1):
        import pdb

        pdb.set_trace()  # noqa: E702
    child_nodes = (nodes[child_id] for (child_id, _) in edges[node.id])
    unvisited_children = [
        node for node in child_nodes if node.times_visited == 0
    ]
    arbitrary_unvisited_child = random.choice(unvisited_children)
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

    assert tree.edges.get(node.id) is None
    tree.edges[node.id] = []
    for action in config.get_all_actions(gamestate):
        child_node = types.Node(
            id=int(random.getrandbits(64)),
            parent_id=node.id,
            times_visited=0,
            value=0,
        )

        # print(child_node.id)
        tree.nodes[child_node.id] = child_node
        tree.edges[node.id].append((child_node.id, action))


def simulate(
    config: types.MctsConfig[G, A],
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    take_action_mut: t.Callable[[G, A], t.Optional[G]],
    gamestate: G,
) -> int:
    # TODO: add decisive move heuristic
    # TODO: use heuristic
    while (result := config.is_over(gamestate)) is None:
        action = random.choice(config.get_all_actions(gamestate))
        take_action_mut(gamestate, action)
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


@contextlib.contextmanager
def action_logger(take_action_mut: t.Callable[[G, A], t.Optional[G]]):
    log = []

    def take_action_mut_with_log(gamestate, action):
        log.append(action)
        return take_action_mut(gamestate, action)

    yield take_action_mut_with_log, log


def undo_actions(
    gamestate: G,
    undo_action: t.Callable[[G, A], t.Optional[G]],
    log: t.List[A],
):
    for action in reversed(log):
        undo_action(gamestate, action)
    return gamestate


# import sys


# def info(type, value, tb):
#     if hasattr(sys, "ps1") or not sys.stderr.isatty():
#         # we are in interactive mode or we don't have a tty-like
#         # device, so we call the default hook
#         sys.__excepthook__(type, value, tb)
#     else:
#         import traceback, pdb

#         # we are NOT in interactive mode, print the exception...
#         traceback.print_exception(type, value, tb)
#         print
#         # ...then start the debugger in post-mortem mode.
#         # pdb.pm() # deprecated
#         pdb.post_mortem(tb)  # more "modern"


# sys.excepthook = info
