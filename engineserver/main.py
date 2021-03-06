# listen on channel for new gamestates
# call N_WALK_BATCH at a time
# feed walk_logs up to server every UPLOAD_WALK_LOG_INTERVAL number of walks
# download tree updates every DOWNLOAD_TREE_UPDATES number of walks

import threading
from queue import Queue, Empty
import typing as t

import engine.typesv1 as eng_types
import engine.mctsv1 as Engine
from engineserver.redis_stream_reader import RedisStreamReader
import common

import redis


ID_LENGTH = 32  # number of bits in a node id

N_WALK_BATCH = 5


G = t.TypeVar("G")  # gamestate
A = t.TypeVar("A")  # action
P = t.TypeVar("P")  # action
Data = t.Dict[str, t.Any]


def listen_for_commands(
    command_queue: Queue, stream_reader: RedisStreamReader
):
    while True:
        commands = stream_reader.read("commands", 0)
        for command in commands:
            command_queue.put(command)


def serve(redis_config: eng_types.RedisConfig) -> A:
    """
    Take a gamestate, run until you get a stop command or a new gamestate
    """

    r = redis.Redis(**redis_config.__dict__)
    stream_reader = RedisStreamReader(r)

    command_queue = Queue()
    command_thread = threading.Thread(
        target=listen_for_commands,
        args=(command_queue, stream_reader),
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

        if command["command_type"] == "new-gamestate":
            rules = common.load_rules(command["game-type"])
            gamestate, gamestate_id, config = (
                rules.decode_gamestate(command["gamestate"]),
                command["gamestate_id"],
                parse_config(command) or config,
            )
            engine = Engine(config)
        elif command["command_type"] == "new-config":
            config = parse_config(command["config"])
        elif command["command_type"] == "stop":
            gamestate = None

        if engine is not None:
            walk_logs, best_move = engine.ponder(gamestate, N_WALK_BATCH)
            upload_to_redis(walk_logs, r, gamestate_id)
            download_from_redis()


def parse_config(data: Data) -> eng_types.MctsConfig:
    # TODO: actually parse data to get players and budget

    rules = common.load_rules(data["game-type"])

    return eng_types.MctsConfig(
        take_action_mut=rules.take_action_mut,
        get_all_actions=rules.get_all_actions,
        is_over=rules.is_over,
        # rollout_policy=rollout_policy,
        get_final_score=rules.get_final_score,
        players=["player"],
        budget=2,
        encode_action=rules.encode_action,
    )


def decode_gamestate(command: t.Dict[str, t.Any]) -> t.Tuple[G, int]:
    game_type = command["game-type"]
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
