# listen on channel for new gamestates
# call N_WALK_BATCH at a time
# feed walk_logs up to server every UPLOAD_WALK_LOG_INTERVAL number of walks
# download tree updates every DOWNLOAD_TREE_UPDATES number of walks

from queue import Queue, Empty
import atexit
import json
import random
import threading
import typing as t

from engine.mctsv1 import Engine
from common.redis_stream_reader import RedisStreamReader
import common.main as common
import common.types as ctypes
import engine.typesv1 as eng_types
import utils

import redis


ID_LENGTH = 32  # number of bits in a node id

N_WALK_BATCH = 5


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # action


def serve(redis_config: eng_types.RedisConfig, engineserver_id: int) -> A:
    """
    Take a gamestate, run until you get a stop command or a new gamestate
    """

    r = redis.Redis(**redis_config.__dict__)
    atexit.register(
        r.flushall
    )  # ideally should wait until all enginservers die

    pubsub = r.pubsub()
    pubsub.subscribe("commands")

    command_queue = Queue()

    def listen_for_commands():
        while True:
            msg = utils.read_chan(pubsub)
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

    rsr = RedisStreamReader(r)
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
            walk_logs, best_move = engine.ponder(gamestate, nseconds=1)
            upload_to_redis(walk_logs, r, gamestate_id, engineserver_id)
            consume_new_walk_logs(rsr, gamestate_id, engine, engineserver_id)
        utils.write_chan(r, "actions", best_move)


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


def try_json_dumps(v):
    try:
        return json.dumps(v)
    except TypeError:
        return v


def upload_to_redis(
    walk_logs: t.List[eng_types.WalkLog],
    r: redis.Redis,
    gamestate_id: int,
    engineserver_id: int,
):
    stream = f"gamestate-{gamestate_id}"
    print(f"upload_to_redis {stream=}")
    with r.pipeline() as pipe:
        for walk_log in walk_logs:
            for item in walk_log:
                item2 = {k: try_json_dumps(v) for k, v in item.items()}
                item2["engineserver_id"] = engineserver_id
                if item2["event-type"] == "new-node":
                    pipe.xadd(stream, item2)
                elif item2["event-type"] == "walk-result":
                    pipe.xadd(stream, item2)
        pipe.execute()


def consume_new_walk_logs(
    rsr: RedisStreamReader,
    gamestate_id: int,
    engine: Engine,
    engineserver_id: int,
):
    stream_name = f"gamestate-{gamestate_id}"
    logs = rsr.read(stream_name)
    engine.consume_walk_log(
        [log for log in logs if log[b"engineserver_id"] != engineserver_id]
    )


if __name__ == "__main__":
    redis_config = eng_types.RedisConfig(
        host="localhost",
        port=6379,
        db=0,
    )
    engineserver_id = random.randbytes(4)
    serve(redis_config, engineserver_id)
