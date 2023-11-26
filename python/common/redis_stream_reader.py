import redis

import collections
import typing as t
import utils


class RedisStreamReader:
    def __init__(self, r: redis.Redis):
        self.r = r
        self.stream_pointers = collections.defaultdict(lambda: "0")

    def read(
        self, stream_name: str, block: t.Optional[int] = None
    ) -> t.List[t.Any]:
        if isinstance(stream_name, str):
            stream_name = stream_name.encode()
        last_id = self.stream_pointers[stream_name]

        ts_item_tuples = utils.read_stream(
            stream_name, self.r, last_id, block=block
        )

        self.stream_pointers[stream_name] = ts_item_tuples[-1][0]

        return [item for (ts, item) in ts_item_tuples]


if __name__ == "__main__":
    redis_config = {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    }

    r = redis.Redis(**redis_config)

    reader = RedisStreamReader(r)
    print(reader.read("commands"))
    r.xadd("commands", {"key4": "val4"})
    print(reader.read("commands"))
    # r.xread({"commands": 0})
