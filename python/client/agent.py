from dataclasses import dataclass
import atexit
import json
import random
import subprocess
import threading
import time
import typing as t

import redis
import redis.client

from engine.mctsv1 import Engine
import common.main as common
import common.types as ctypes
import engine.typesv1 as eng_types
import utils


AGENT_TYPES = [
    "random",
    "mcts-local",
    "mcts-distributed",
    "minimax",
    "human",
]

AgentType = t.Union[
    t.Literal["random"],
    t.Literal["mcts-local"],
    t.Literal["mcts-distributed"],
    t.Literal["minimax"],
    t.Literal["human"],
]


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # action


@dataclass
class Agent(t.Generic[G, A, P]):
    agent_type: AgentType
    get_action: t.Callable[[G], A]


def get_agent(
    agent_type: AgentType, game_type: str, mcts_budget=1, n_engine_servers=2
) -> Agent:
    rules = common.load_rules(game_type)

    config = eng_types.MctsConfig(
        take_action_mut=rules.take_action_mut,
        get_all_actions=rules.get_all_actions,
        is_over=rules.is_over,
        get_final_score=rules.get_final_score,
        players=rules.get_players(),
        encode_action=rules.encode_action,
        decode_action=rules.decode_action,
    )

    if agent_type == "random":

        def get_action(gamestate: G) -> A:
            random_action = rules.get_random_action(gamestate)
            if random_action is None:
                utils.assert_never(
                    "Random action is None even though game is not over"
                )
            return random_action

        return Agent(
            agent_type=agent_type,
            get_action=get_action,
        )

    elif agent_type == "human":
        return Agent(
            get_action=rules.get_action_from_human, agent_type=agent_type
        )
    elif agent_type == "mcts-local":

        def get_action(gamestate: G) -> A:
            engine = Engine(config, gamestate)
            _, action = engine.ponder(100)
            return action

        return Agent(get_action=get_action, agent_type=agent_type)
    elif agent_type == "mcts-distributed":
        return EngineServerFarmClient(
            agent_type, game_type, n_engine_servers, timeout=mcts_budget
        )
    else:
        utils.assert_never(f"Invalid agent type {agent_type}")


# type of agent
class EngineServerFarmClient(t.Generic[G, A]):
    """
    Client to the engine servers. Engine servers run in aws. This class posts
    commands to redis and streams responses. Spawns a thread to listen to
    pyredis
    """

    def __init__(
        self,
        agent_type: AgentType,
        game_type: str,
        n_engine_servers: int,
        timeout: int,
    ) -> Agent:
        self.agent_type = agent_type
        # TODO: launch redis
        # TODO: launch engine servers in ecs
        # self.procs = self._launch_engine_servers_local(n_engine_servers)
        self.rules = common.load_rules(game_type)
        self.game_type = game_type
        self.timeout = timeout

        self.r = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
        )
        self.r.flushall()

        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe("actions")

        atexit.register(
            lambda: utils.write_chan(self.r, "commands", ctypes.Stop())
        )

    def _launch_engine_servers_local(self, n_engine_servers: int):
        procs = [
            subprocess.Popen(["python", "engineserver/main.py"])
            for _ in range(n_engine_servers)
        ]

        def killall():
            for p in procs:
                p.kill()

        atexit.register(killall)
        return procs

    def get_action(self, gamestate: G) -> A:
        """
        Send this gamestate to redis, wait <timeout> seconds and return
        whatever action ends up in redis
        """
        gamestate_id = random.getrandbits(64)
        utils.write_chan(
            self.r,
            "commands",
            ctypes.NewGamestate(
                command_type="new-gamestate",
                game_type=self.game_type,
                gamestate_id=gamestate_id,
                gamestate=gamestate.__dict__,
            ),
        )

        def event_stream(interval):
            while True:
                yield utils.read_chan(self.pubsub, interval)

        msg_stream = (
            msg
            for msg in event_stream(interval=0.1)
            if msg is None or msg["gamestate_id"] == gamestate_id
        )
        messages = utils.collect(
            msg_stream, min_time=self.timeout, max_time=max(self.timeout, 5)
        )
        if messages is None:
            utils.print_err(
                f"Failed to receive message from engineservers "
                f"after timeout of {max(self.timeout, 5)}",
                exit=True,
            )
        actions = [
            a["best_move"]
            for a in messages
            if a["gamestate_id"] == gamestate_id
        ]
        print([a["gamestate_id"] for a in messages])
        assert (
            len(actions) > 0
        ), f"No engineserver responded with actions for gamestate id {gamestate_id}"
        return actions[-1]
        # return utils.read_chan(self.pubsub)
