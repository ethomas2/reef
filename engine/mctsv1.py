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

    def __init__(self):
        self.this_run = []
        self.data = {
            "runs": [self.this_run],
        }

    def add_root(self, root_id: int, gamestate: G):
        assert (
            "root" not in self.data
        ), "add_root should only be called once per logger"
        self.data["root"] = {"root_id": root_id, "gamestate": gamestate}

    def new_run(self):
        self.this_run = []
        self.data["runs"].append(self.this_run)

    def ucb_choice(self, parent_node_id: int, child_node_id: int, action: A):
        self.this_run.append(
            {
                "type": "ucb choice",
                "parent_id": parent_node_id,
                "child_id": child_node_id,
                "action": action,
            }
        )

    def result(self, node_id: int, result: float):
        self.this_run.append(
            {"type": "result", "node_id": node_id, "result": result}
        )

    def expand(
        self, parent_id: int, children: t.List[t.Tuple[types.NodeId, A]]
    ):
        self.this_run.append(
            {
                "type": "expand",
                "parent_id": parent_id,
                "child_id_action_pairs": children,
            }
        )

    def full_tree(self, tree: types.Tree[G, A]):
        self.data["final_tree"] = tree

    def flush(self, filepath=None):
        with contextlib.ExitStack() as stack:
            if filepath is None:
                output = sys.stdout
            else:
                output = stack.enter_context(open(filepath, "w+"))

            output.write(json.dumps(self.data, cls=DataclassEncoder))

    def clear(self):
        self.this_run = []
        self.data = {"runs": [], "tree": {}}


def mcts_v1(config: types.MctsConfig[G, A], gamestate: G) -> A:
    start = time.time()
    end = start + config.budget
    root = types.Node(
        id=0,
        parent_id=-1,
        times_visited=0,
        wins_vec={p: 0 for p in config.players},
        player=gamestate.player,
    )
    tree = types.Tree(nodes={root.id: root}, edges={})

    logger = MctsLogger()
    logger.add_root(root.id, gamestate)

    gamestate_copy = copy.deepcopy(gamestate)  # TODO: remove
    player = gamestate.player
    while time.time() < end:
        with action_logger(config.take_action_mut) as (take_action_mut, log):
            leaf_node = tree_policy(
                config, logger, root, tree, take_action_mut, gamestate
            )
            leaf_id = leaf_node.id
            winning_player = simulate(
                config,
                logger,
                leaf_node,
                tree,
                take_action_mut,
                gamestate,
            )
            logger.result(leaf_id, winning_player)
            backup(config, logger, tree, leaf_node, winning_player)
            assert gamestate != gamestate_copy
            undo_actions(gamestate, config.undo_action, log)
        assert gamestate == gamestate_copy
        logger.new_run()
    logger.full_tree(tree)
    logger.flush(LOGFILE)

    child_action_pairs = (
        (tree.nodes[child_id], action)
        for (child_id, action) in tree.edges[root.id]
    )
    action_value_pairs = [
        (action, child.wins_vec[player] / float(child.times_visited))
        for (child, action) in child_action_pairs
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

        # if node has an unvisited child, return the unvisited child
        unvisited_children = [
            nodes[child_id]
            for (child_id, _) in children
            if nodes[child_id].times_visited == 0
        ]
        if len(unvisited_children) > 0:
            return random.choice(unvisited_children)

        # otherwise walk down the tree via ucb
        child_id, action = max(
            children,
            key=lambda child_id_action: ucb(
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


def ucb(
    config: types.MctsConfig, tree: types.Tree, node: types.Node, player: P
) -> float:
    xj = node.wins_vec[player] / node.times_visited
    parent = tree.nodes[node.parent_id]
    explore_term = config.C * math.sqrt(
        math.log(parent.times_visited) / float(node.times_visited)
    )
    return xj + explore_term


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

    player_idx = config.players.index(gamestate.player)
    for action in config.get_all_actions(gamestate):
        child_node = types.Node(
            id=int(random.getrandbits(64)),
            parent_id=node.id,
            times_visited=0,
            wins_vec={p: 0 for p in config.players},
            # TODO: making the assumption here that it's always the next person
            # in the list's turn. Instead we should take the action, see whose
            # turn it ends up being, and undo it immediately afterwards. Or
            # return the player whose turn it is in get_all_actions
            player=config.players[(player_idx + 1) % len(config.players)],
        )

        nodes[child_node.id] = child_node
        edges[node.id].append((child_node.id, action))

    logger.expand(node.id, tree.edges[node.id])


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
    winning_player: P,
):
    while node is not None:
        node.times_visited += 1
        # winning_player could be "draw". Should includ that in the type
        if winning_player in node.wins_vec:
            node.wins_vec[winning_player] += 1
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
