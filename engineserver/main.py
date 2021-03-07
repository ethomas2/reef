# listen on channel for new gamestates
# call N_WALK_BATCH at a time
# feed walk_logs up to server every UPLOAD_WALK_LOG_INTERVAL number of walks
# download tree updates every DOWNLOAD_TREE_UPDATES number of walks

from queue import Queue, Empty
import threading
import typing as t

import engine.typesv1 as eng_types
from engine.mctsv1 import Engine
import common.main as common
import common.types as ctypes
import utils

import redis


ID_LENGTH = 32  # number of bits in a node id

N_WALK_BATCH = 5


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # action
Data = t.Dict[str, t.Any]


def serve(redis_config: eng_types.RedisConfig) -> A:
    """
    Take a gamestate, run until you get a stop command or a new gamestate
    """

    r = redis.Redis(**redis_config.__dict__)
    pubsub = r.pubsub()
    pubsub.subscribe("commands")

    command_queue = Queue()

    def listen_for_commands():
        while True:
            msg = utils.get_message(pubsub)
            command_queue.put(msg)

    command_thread = threading.Thread(
        target=listen_for_commands,
        daemon=True,
    )
    command_thread.start()

    engine, gamestate, config = (
        None,
        None,
        None,
    )

    while True:
        try:
            command = (
                command_queue.get(block=True)
                if gamestate is None
                else command_queue.get(block=False)
            )
        except Empty:
            pass

        if isinstance(command, ctypes.NewGamestate):
            rules = common.load_rules(command.game_type)
            gamestate, gamestate_id, config = (
                rules.decode_gamestate(command.gamestate),
                command.gamestate_id,
                parse_config(command) or config,
            )
            engine = Engine(config)
        elif isinstance(command, ctypes.NewConfig):
            utils.print_err("Command NewConfig is unimplemented")
        elif isinstance(command, ctypes.Stop):
            gamestate = None
        else:
            utils.print_err(f"unknown command_type {type(command)}\n{command}")

        if engine is not None:
            walk_logs, best_move = engine.ponder(gamestate, N_WALK_BATCH)
            upload_to_redis(walk_logs, r, gamestate_id)
            download_from_redis()
        utils.publish(r, "actions", best_move)


def parse_config(command: ctypes.NewGamestate) -> eng_types.MctsConfig:
    # TODO: actually parse data to get players and budget

    rules = common.load_rules(command.game_type)

    return eng_types.MctsConfig(
        take_action_mut=rules.take_action_mut,
        get_all_actions=rules.get_all_actions,
        is_over=rules.is_over,
        # rollout_policy=rollout_policy,
        get_final_score=rules.get_final_score,
        players=["player"],
        encode_action=rules.encode_action,
    )


def decode_gamestate(command: t.Dict[str, t.Any]) -> t.Tuple[G, int]:
    game_type = command["game_type"]
    gamestate_id = command["gamestate_id"]
    rules = common.load_rules(game_type)
    gamestate = rules.decode_gamestate(command["gamestate"])

    return gamestate, gamestate_id


def upload_to_redis(
    walk_logs: t.List[eng_types.WalkLog], r: redis.Redis, gamestate_id: int
):
    stream = f"gamestate-{gamestate_id}"
    with r.pipeline() as pipe:
        for walk_log in walk_logs:
            for item in walk_log:
                if item["event-type"] == "new-node":
                    pipe.xadd(stream, item)
                elif item["event-type"] == "walk-result":
                    pipe.xadd(stream, "walk result")
        pipe.execute()


def download_from_redis():
    pass


if __name__ == "__main__":
    redis_config = eng_types.RedisConfig(
        host="localhost",
        port=6379,
        db=0,
    )
    serve(redis_config)
