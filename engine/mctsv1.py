import copy
import hashlib
import math
import random
import time
import typing as t

import engine.typesv1 as types


# import wandb


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # player
WalkLog = t.List[t.Dict[str, t.Any]]

MAX_STEPS = 10000

ID_LENGTH = 32  # number of bits in a node id


def mcts_v1(config: types.MctsConfig[G, A], root_gamestate: G) -> A:
    root = types.Node(
        id=(0).to_bytes(ID_LENGTH, "big"),
        parent_id=-1,
        times_visited=0,
        score_vec={p: 0 for p in config.players},
    )
    tree = types.Tree(nodes={root.id: root}, edges={})
    gamestate = copy.deepcopy(root_gamestate)

    nwalks = 0
    start = time.time()
    end = start + config.budget
    while time.time() < end:
        walk_log = walk(config, root, tree, gamestate)
        gamestate = restore_gamestate(
            config, root_gamestate, gamestate, walk_log
        )
        assert gamestate == root_gamestate
        upload_to_redis(walk_log)
        nwalks += 1

    action = pick_best_action(tree, root_gamestate.player, root.id)

    return action


def walk(
    config: types.MctsConfig[G, A],
    root: types.Node[A],
    tree: types.Tree[G, A],
    gamestate: G,
):
    walk_log = []  # walk log will be mutated
    ctx = {
        "config": config,
        "walk_log": walk_log,
        "tree": tree,
        "gamestate": gamestate,  # mutated by tree_policy & rollout
    }
    node = tree_policy(root=root, **ctx)
    score_vec = rollout(node=node, **ctx)
    backup(node=node, score_vec=score_vec, **ctx)
    return walk_log


def tree_policy(
    root: types.Node[A],
    config: types.MctsConfig[G, A],
    walk_log: WalkLog,
    tree: types.Tree[G, A],
    gamestate: G,
) -> types.Node[A]:
    nodes, edges = tree.nodes, tree.edges

    ucb_fn = {
        None: ucb_basic,
        "pre-visit": ucb_with_pre_visit_heuristic,
        "simple": ucb_with_simple_heuristic,
    }[config.heuristic_type]

    node = root
    for _ in range(MAX_STEPS):
        # If node hasn't been expanded, expand it
        if edges.get(node.id) is None:
            expand(config, walk_log, tree, node, gamestate)
            assert edges.get(node.id) is not None
            child_nodes = [nodes[child_id] for (child_id, _) in edges[node.id]]
            if len(child_nodes) == 0:
                return node
            return random.choice(child_nodes)

        children = edges[node.id]

        # if this is a terminal node, return it
        if children == []:
            return node

        # otherwise walk down the tree via ucb
        if gamestate.player == "environment":
            child_id, action = random.choice(children)
        else:
            child_id, action = max(
                children,
                key=lambda child_id_action: ucb_fn(
                    config,
                    tree,
                    nodes[child_id_action[0]],
                    gamestate.player,
                ),
            )
        assert nodes.get(child_id) is not None
        walk_log.append({"event_type": "tree-policy-action", "action": action})
        gamestate = config.take_action_mut(gamestate, action)
        node = nodes[child_id]
    raise Exception(f"tree_policy exceeded {MAX_STEPS} steps")


def ucb_basic(
    config: types.MctsConfig, tree: types.Tree, node: types.Node, player: P
) -> float:
    if node.times_visited == 0:
        return float("inf")
    xj = node.score_vec[player] / node.times_visited
    parent = tree.nodes[node.parent_id]
    explore_term = config.C * math.sqrt(
        math.log(parent.times_visited) / float(node.times_visited)
    )
    return xj + explore_term


def ucb_with_pre_visit_heuristic(
    config: types.MctsConfig, tree: types.Tree, node: types.Node, player: P
) -> float:
    """
    Like ucb but adds heuristic. Pretends each node has already been visited n
    times with a reward of k each time.
    """
    n, k = node.heuristic_val.denominator, node.heuristic_val.numerator
    assert config.heuristic is not None
    assert config.heuristic_type == "pre-visit"
    assert n > 0
    assert 0 <= k <= n, k
    xj = (node.score_vec[player] + k) / (node.times_visited + n)
    parent = tree.nodes[node.parent_id]
    num_siblings = len(tree.edges[parent.id])
    explore_term = config.C * math.sqrt(
        math.log(parent.times_visited + n * num_siblings)
        / float(node.times_visited + n)
    )
    return xj + explore_term


def ucb_with_simple_heuristic(
    config: types.MctsConfig, tree: types.Tree, node: types.Node, player: P
) -> float:
    assert config.heuristic_type == "basic"
    assert config.heuristic is not None
    return ucb_basic(config, tree, node, player) + node.heuristic


def expand(
    config: types.MctsConfig[G, A],
    walk_log: WalkLog,
    tree: types.Tree,
    node: types.Node,
    gamestate: G,
):
    """
    Add children to node. Should only be called on node that doesn't have
    children already (i.e. called once per node. Different definition than
    definition of expand in wikipedia
    """
    nodes, edges = tree.nodes, tree.edges

    assert edges.get(node.id) is None
    tree.edges[node.id] = []

    if config.is_over(gamestate) is not None:
        return

    for action in config.get_all_actions(gamestate):
        m = hashlib.md5()  # parent id
        m.update(node.id)
        m.update(config.encode_action(action).encode())
        id = m.digest()

        child_node = types.Node(
            id=id,
            parent_id=node.id,
            times_visited=0,
            score_vec={p: 0 for p in config.players},
            heuristic_val=(
                None
                if config.heuristic_type is None
                else types.HeuristicVal(5 * config.heuristic(gamestate), 5)
            ),
        )
        assert (
            child_node.id not in nodes
        ), f"nnodes {len(tree.nodes)} id {child_node.id}"

        nodes[child_node.id] = child_node
        edges[node.id].append((child_node.id, action))


def rollout(
    node: types.Node[A],
    config: types.MctsConfig[G, A],
    walk_log: WalkLog,
    tree: t.Dict[int, t.List[types.Node[A]]],
    gamestate: G,
) -> types.ScoreVec:
    if config.rollout_policy is not None:
        score_vec = config.rollout_policy(gamestate)
    else:
        winning_player = simulate(config, walk_log, node, tree, gamestate)
        score_vec = (
            config.get_final_score(gamestate)
            if config.get_final_score is not None
            else {p: int(p == winning_player) for p in config.players}
        )
    assert set(score_vec.keys()) == set(config.players)
    return score_vec


def simulate(
    config: types.MctsConfig[G, A],
    walk_log: WalkLog,
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    gamestate: G,
) -> P:
    # TODO: add decisive move heuristic
    c = 0
    while (result := config.is_over(gamestate)) is None:
        if c >= MAX_STEPS:
            raise Exception(f"Simulate exceeded {MAX_STEPS} steps")
        action = random.choice(config.get_all_actions(gamestate))
        config.take_action_mut(gamestate, action)
        walk_log.append({"event_type": "simulation-action", "action": action})
        c += 1
    assert config.is_over(gamestate) is not None
    return result


def backup(
    node: types.Node,
    score_vec: types.ScoreVec,
    config: types.MctsConfig,
    walk_log: WalkLog,
    tree: types.Tree[G, A],
    gamestate: G,
):
    """ Update node statistics """
    assert all(0 <= v <= 1 for v in score_vec.values())
    assert set(score_vec.keys()) == set(config.players)
    while node is not None:
        node.times_visited += 1
        for key, val in score_vec.items():
            node.score_vec[key] += val

        node = tree.nodes.get(node.parent_id)


def restore_gamestate(
    config: types.MctsConfig[G, A],
    root_gamestate: G,
    current_gamestate: G,
    walk_log: WalkLog,
):
    if config.undo_action is not None:
        actions = [
            entry["action"]
            for entry in walk_log
            if entry["event_type"]
            in ["tree-policy-action", "simulation-action"]
        ]
        for action in reversed(actions):
            config.undo_action(current_gamestate, action)
        return current_gamestate
    else:
        return copy.deepcopy(root_gamestate)


def pick_best_action(tree: types.Tree[G, A], player: P, root_id):
    root = tree.nodes[root_id]
    child_action_pairs = (
        (tree.nodes[child_id], action)
        for (child_id, action) in tree.edges[root.id]
    )

    action_value_pairs = [
        (action, child.score_vec[player] / float(child.times_visited))
        for (child, action) in child_action_pairs
        if child.times_visited > 0  # this shouldn't happen
    ]

    action, _ = max(action_value_pairs, key=lambda x: x[1])
    return action


def upload_to_redis(log):
    pass
