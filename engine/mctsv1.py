import copy
import hashlib
import math
import random
import time
import typing as t

import redis

import engine.typesv1 as types
import utils


# import wandb


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # player

MAX_STEPS = 10000

ID_LENGTH = 4  # number of bytes in a node id
assert ID_LENGTH <= 20, "ID_LENGTH must be <= the size of an md5 hash (20)"


class Engine(t.Generic[G, A, P]):
    def __init__(
        self,
        config: types.MctsConfig[G, A],
        gamestate: G,
    ) -> t.Tuple[t.List[types.WalkLog], A]:
        self.config = config
        self.root_gamestate = gamestate

        self.root_node = types.Node(
            id=0,
            parent_id=-1,
            times_visited=0,
            score_vec={p: 0 for p in self.config.players},
        )
        self.tree = types.Tree(
            nodes={self.root_node.id: self.root_node}, edges={}
        )

    def ponder(
        self,
        n_walks: int,
    ) -> t.Tuple[t.List[types.WalkLog], A]:

        walk_logs = []
        for _ in range(n_walks):
            walk_log = self._walk()
            walk_logs.append(walk_log)

        action = self._pick_best_action(
            self.tree, self.root_gamestate.player, self.root_node.id
        )

        return walk_logs, action

    def consume_walk_log(self, walk_log: types.WalkLog):
        for item in walk_log:
            if item["event-type"] == "new-node":
                if item["id"] in self.tree.nodes:
                    continue
                else:
                    self._new_node(
                        id=item["id"],
                        parent_id=item["parent_id"],
                        action=item["action"],
                    )

            elif item["event-type"] == "walk-result":
                pass
                # raise NotImplementedError
            else:
                utils.assert_never(
                    f"Unknown walk_log event-type {item['event-type']}"
                )

    def _new_node(self, id, parent_id, action, previsit_heuristic_val=None):
        """
        This method temporarily brakes the invariant that a node either has all
        it's children in teh tree or none of it's children (with None)
        """
        nodes, edges = self.tree.nodes, self.tree.edges
        child_node = types.Node(
            id=id,
            parent_id=parent_id,
            times_visited=0,
            score_vec={p: 0 for p in self.config.players},
            heuristic_val=previsit_heuristic_val,
        )
        assert (
            child_node.id not in nodes
        ), f"nnodes {len(self.tree.nodes)} id {child_node.id}"
        nodes[child_node.id] = child_node
        # TODO: is this safe? We want to maintain the invariant that either all
        # of a nodes children are in the tree or children(parent) = None
        edges.setdefault(parent_id, [])
        edges[parent_id].append((child_node.id, action))
        return child_node

    def _walk(self) -> types.WalkLog:
        gamestate = copy.deepcopy(self.root_gamestate)
        walk_log = []  # walk log will be mutated
        node = self._tree_policy(walk_log, gamestate)
        score_vec = self._rollout(node, walk_log, gamestate)
        self._backup(node, score_vec, gamestate, walk_log)
        gamestate = self._restore_gamestate(gamestate, walk_log)
        assert gamestate == self.root_gamestate
        return walk_log

    def _tree_policy(
        self,
        walk_log: types.WalkLog,
        gamestate: G,
    ) -> types.Node[A]:
        nodes, edges = self.tree.nodes, self.tree.edges

        ucb_fn = {
            None: _ucb_basic,
            "pre-visit": _ucb_with_pre_visit_heuristic,
            "simple": _ucb_with_simple_heuristic,
        }[self.config.heuristic_type]

        node = self.root_node
        for _ in range(MAX_STEPS):
            # If node hasn't been expanded, expand it
            if edges.get(node.id) is None:
                self._expand(walk_log, node, gamestate)
                assert edges.get(node.id) is not None
                child_nodes = [
                    nodes[child_id] for (child_id, _) in edges[node.id]
                ]
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
                        self.config.C,
                        self.tree,
                        nodes[child_id_action[0]],
                        gamestate.player,
                    ),
                )
            assert nodes.get(child_id) is not None
            walk_log.append({"event-type": "take-action", "action": action})
            gamestate = self.config.take_action_mut(gamestate, action)
            node = nodes[child_id]
        raise Exception(f"tree_policy exceeded {MAX_STEPS} steps")

    def _expand(
        self,
        walk_log: types.WalkLog,
        node: types.Node,
        gamestate: G,
    ):
        """
        Add children to node. Should only be called on node that doesn't have
        children already (i.e. called once per node. Different definition than
        definition of expand in wikipedia
        """

        assert self.tree.edges.get(node.id) is None
        self.tree.edges[node.id] = []

        if self.config.is_over(gamestate) is not None:
            return

        for action in self.config.get_all_actions(gamestate):
            m = hashlib.md5()  # parent id
            m.update(int.to_bytes(node.id, ID_LENGTH, "big"))
            m.update(self.config.encode_action(action).encode())
            id = int.from_bytes(m.digest()[:ID_LENGTH], "big")

            child_node = self._new_node(
                id,
                node.id,
                action,
                (
                    None
                    if self.config.heuristic_type is None
                    else types.HeuristicVal(
                        5 * self.config.heuristic(gamestate), 5
                    )
                ),
            )

            walk_log.append(
                {
                    "event-type": "new-node",
                    "id": child_node.id,
                    "parent_id": child_node.parent_id,
                    "action": action,
                }
            )

    def _rollout(
        self,
        node: types.Node[A],
        walk_log: types.WalkLog,
        gamestate: G,
    ) -> types.ScoreVec:
        if self.config.rollout_policy is not None:
            score_vec = self.config.rollout_policy(gamestate)
        else:
            winning_player = self._simulate(walk_log, node, gamestate)
            score_vec = (
                self.config.get_final_score(gamestate)
                if self.config.get_final_score is not None
                else {p: int(p == winning_player) for p in self.config.players}
            )
        assert set(score_vec.keys()) == set(self.config.players)
        walk_log.append({"event-type": "walk-result", "score": score_vec})
        return score_vec

    def _simulate(
        self,
        walk_log: types.WalkLog,
        node: types.Node[A],
        gamestate: G,
    ) -> P:
        # TODO: add decisive move heuristic
        c = 0
        while (result := self.config.is_over(gamestate)) is None:
            if c >= MAX_STEPS:
                raise Exception(f"Simulate exceeded {MAX_STEPS} steps")
            action = random.choice(self.config.get_all_actions(gamestate))
            self.config.take_action_mut(gamestate, action)
            walk_log.append({"event-type": "take-action", "action": action})
            c += 1
        assert self.config.is_over(gamestate) is not None
        return result

    def _backup(
        self,
        node: types.Node,
        score_vec: types.ScoreVec,
        gamestate: G,
        walk_log: types.WalkLog,
    ):
        """ Update node statistics """
        assert all(0 <= v <= 1 for v in score_vec.values())
        assert set(score_vec.keys()) == set(self.config.players)
        while node is not None:
            node.times_visited += 1
            for key, val in score_vec.items():
                node.score_vec[key] += val

            node = self.tree.nodes.get(node.parent_id)

    def _restore_gamestate(
        self,
        current_gamestate: G,
        walk_log: types.WalkLog,
    ):
        if self.config.undo_action is not None:
            actions = [
                entry["action"]
                for entry in walk_log
                if entry["event-type"] == "take-action"
            ]
            for action in reversed(actions):
                self.config.undo_action(current_gamestate, action)
            return current_gamestate
        else:
            return copy.deepcopy(self.root_gamestate)

    def _pick_best_action(self, tree: types.Tree[G, A], player: P, root_id):
        root = self.tree.nodes[root_id]
        child_action_pairs = (
            (self.tree.nodes[child_id], action)
            for (child_id, action) in self.tree.edges[root.id]
        )

        action_value_pairs = [
            (action, child.score_vec[player] / float(child.times_visited))
            for (child, action) in child_action_pairs
            if child.times_visited > 0  # this shouldn't happen
        ]

        action, _ = max(action_value_pairs, key=lambda x: x[1])
        return action


def _ucb_basic(
    C: float, tree: types.Tree, node: types.Node, player: P
) -> float:
    if node.times_visited == 0:
        return float("inf")
    xj = node.score_vec[player] / node.times_visited
    parent = tree.nodes[node.parent_id]
    explore_term = C * math.sqrt(
        math.log(parent.times_visited) / float(node.times_visited)
    )
    return xj + explore_term


def _ucb_with_pre_visit_heuristic(
    C: float, tree: types.Tree, node: types.Node, player: P
) -> float:
    """
    Like ucb but adds heuristic. Pretends each node has already been visited n
    times with a reward of k each time.
    """
    n, k = node.heuristic_val.denominator, node.heuristic_val.numerator
    # assert self.config.heuristic is not None
    # assert self.config.heuristic_type == "pre-visit"
    assert n > 0
    assert 0 <= k <= n, k
    xj = (node.score_vec[player] + k) / (node.times_visited + n)
    parent = tree.nodes[node.parent_id]
    num_siblings = len(tree.edges[parent.id])
    explore_term = C * math.sqrt(
        math.log(parent.times_visited + n * num_siblings)
        / float(node.times_visited + n)
    )
    return xj + explore_term


def _ucb_with_simple_heuristic(
    C: float, tree: types.Tree, node: types.Node, player: P
) -> float:
    # assert self.config.heuristic_type == "basic"
    # assert self.config.heuristic is not None
    return _ucb_basic(C, tree, node, player) + node.heuristic
