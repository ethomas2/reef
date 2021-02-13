import contextlib
import copy
import dataclasses
import json
import math
import random
import sys
import time
import typing as t

import engine.typesv1 as types


import wandb


G = t.TypeVar("G")
A = t.TypeVar("A")
P = t.TypeVar("P")  # player

MAX_STEPS = 10000
LOGFILE = "scrap/mcts-run"


class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return o.__dict__
        return o


class MctsLogger:
    """
    Auxilary logging only. Action logging is done by a differnet thing since
    that's necessary for correctness
    """

    def __init__(self, log_whiltelist=None, on=True):
        self.on = on
        if not self.on:
            return
        self.gs_num = 0
        self.run_num = 0
        wandb.init("mcts-tracking")

    def new_gs(self, root_id: int, gamestate: G):
        if not self.on:
            return
        self.gs_num += 1
        self.run_num = 0

    def new_run(self):
        if not self.on:
            return
        self.run_num += 1

    def ucb_choice(self, parent_node_id: int, child_node_id: int, action: A):
        if not self.on:
            return
        wandb.log(
            {
                "type": "ucb choice",
                "gs": self.gs_num,
                "run": self.run_num,
                "parent_id": parent_node_id,
                "child_id": child_node_id,
                "action": (
                    action.__dict__
                    if dataclasses.is_dataclass(action)
                    else action
                ),
            }
        )

    def result(self, node_id: int, result: float):
        if not self.on:
            return
        wandb.log(
            {
                "type": "result",
                "gs": self.gs_num,
                "run": self.run_num,
                "node_id": node_id,
                "result": result,
            }
        )

    def expand(
        self, parent_id: int, children: t.List[t.Tuple[types.NodeId, A]]
    ):
        if not self.on:
            return
        wandb.log(
            {
                "type": "expand",
                "gs": self.gs_num,
                "run": self.run_num,
                "parent_id": parent_id,
                "child_id_action_pairs": [
                    (
                        node_id,
                        action.__dict__
                        if dataclasses.is_dataclass(action)
                        else action,
                    )
                    for (node_id, action) in children
                ],
            }
        )

    def full_tree(self, tree: types.Tree[G, A]):
        if not self.on:
            return
        pass
        # if not (
        #     "full_tree" in self.log_whiltelist or "*" in self.log_whiltelist
        # ):
        #     return
        # self.data["final_tree"] = tree


logger = MctsLogger(on=False)


def mcts_v1(config: types.MctsConfig[G, A], root_gamestate: G) -> A:
    start = time.time()
    end = start + config.budget
    root = types.Node(
        id=0,
        parent_id=-1,
        times_visited=0,
        score_vec={p: 0 for p in config.players},
        # player=root_gamestate.player,
    )
    tree = types.Tree(nodes={root.id: root}, edges={})

    logger.new_gs(root.id, root_gamestate)

    gamestate = copy.deepcopy(root_gamestate)  # TODO: remove
    player = gamestate.player
    while time.time() < end:
        with action_logger(config.take_action_mut) as (take_action_mut, log):
            leaf_node = tree_policy(
                config, logger, root, tree, take_action_mut, gamestate
            )
            leaf_id = leaf_node.id
            score_vec = rollout(
                config, logger, leaf_node, tree, take_action_mut, gamestate
            )
            backup(config, logger, tree, leaf_node, score_vec, gamestate)
            logger.result(leaf_id, score_vec)
            # assert gamestate != gamestate_copy
            if config.undo_action is not None:
                undo_actions(gamestate, config.undo_action, log)
            else:
                gamestate = copy.deepcopy(root_gamestate)
        assert gamestate == root_gamestate
        logger.new_run()
    logger.full_tree(tree)

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


def tree_policy(
    config: types.MctsConfig[G, A],
    logger: MctsLogger,
    root: types.Node[A],
    tree: types.Tree[G, A],
    take_action_mut: t.Callable[[G, A], t.Optional[G]],
    gamestate: G,
) -> (types.Node[A], bool):
    nodes, edges = tree.nodes, tree.edges

    ucb_fn = {
        None: ucb_basic,
        "pre-visit": ucb_with_pre_visit_heuristic,
        "simple": ucb_with_simple_heuristic,
    }[config.heuristic_type]

    node = root
    for _ in range(MAX_STEPS):
        # If node hasn't been expanded, expand it
        children = edges.get(node.id)
        if children is None:
            expand(config, logger, tree, node, gamestate)
            child_id_action_pairs = edges.get(node.id)
            assert child_id_action_pairs is not None
            child_nodes = [
                nodes[child_id] for (child_id, _) in child_id_action_pairs
            ]
            if len(child_nodes) == 0:
                return node
            return random.choice(child_nodes)

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
        logger.ucb_choice(node.id, child_id, action)
        gamestate = take_action_mut(gamestate, action)
        node = nodes.get(child_id)
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
    logger: MctsLogger,
    tree: types.Tree,
    node: types.Node,
    gamestate: G,
):
    nodes, edges = tree.nodes, tree.edges

    assert edges.get(node.id) is None
    tree.edges[node.id] = []

    if config.is_over(gamestate) is not None:
        return

    for action in config.get_all_actions(gamestate):

        # not using a logging take_action_mut here on purpose
        child_node = types.Node(
            id=int(random.getrandbits(32)),
            parent_id=node.id,
            times_visited=0,
            score_vec={p: 0 for p in config.players},
            heuristic_val=(
                None
                if config.heuristic_type is None
                else types.HeuristicVal(5 * config.heuristic(gamestate), 5)
            ),
        )

        nodes[child_node.id] = child_node
        edges[node.id].append((child_node.id, action))

    logger.expand(node.id, tree.edges[node.id])


def rollout(
    config: types.MctsConfig[G, A],
    logger: MctsLogger,
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    take_action_mut: t.Callable[[G, A], t.Optional[G]],
    gamestate: G,
) -> types.ScoreVec:
    if config.rollout_policy is not None:
        return config.rollout_policy(gamestate)
    else:
        winning_player = simulate(
            config, logger, node, tree, take_action_mut, gamestate
        )
        # gamestate has bene mutated by simulate
        final_score = config.final_score and config.final_score(gamestate)
        score_vec = (
            final_score
            if final_score is not None
            else {p: int(p == winning_player) for p in config.players}
        )
        return score_vec


def simulate(
    config: types.MctsConfig[G, A],
    logger: MctsLogger,
    node: types.Node[A],
    tree: t.Dict[int, t.List[types.Node[A]]],
    take_action_mut: t.Callable[[G, A], t.Optional[G]],
    gamestate: G,
) -> P:
    # TODO: add decisive move heuristic
    # TODO: use heuristic
    c = 0
    while (result := config.is_over(gamestate)) is None:
        if c >= MAX_STEPS:
            raise Exception(f"Simulate exceeded {MAX_STEPS} steps")
        action = random.choice(config.get_all_actions(gamestate))
        take_action_mut(gamestate, action)
        c += 1
    return result


def backup(
    config: types.MctsConfig,
    logger: MctsLogger,
    tree: types.Tree[G, A],
    node: types.Node,
    score_vec: types.ScoreVec,
    gamestate: G,
):
    # assert config.is_over(gamestate)
    assert all(0 <= v <= 1 for v in score_vec.values())
    assert set(score_vec.keys()) == set(config.players)
    while node is not None:
        node.times_visited += 1
        for key, val in score_vec.items():
            node.score_vec[key] += val

        node = tree.nodes.get(node.parent_id)


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
