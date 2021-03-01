import redis

import collections
import typing as t


class RedisStreamReader:
    def __init__(self, r: redis.Redis):
        self.r = r
        self.stream_pointers = collections.defaultdict(lambda: "0")

    def read(self, stream_name: str, block: t.Optional[int] = None):
        if isinstance(stream_name, str):
            stream_name = stream_name.encode()
        last_id = self.stream_pointers[stream_name]
        result = self.r.xread({stream_name: last_id}, block=block)
        item_ts_tuples = next(
            (
                stream_items
                for result_stream_name, stream_items in result
                if result_stream_name == stream_name
            ),
            None,
        )
        if item_ts_tuples is None or item_ts_tuples == []:
            return None

        self.stream_pointers[stream_name] = [
            ts for ts, item in item_ts_tuples
        ][-1]
        return [item for ts, item in item_ts_tuples]


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
