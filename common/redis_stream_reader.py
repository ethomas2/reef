import redis

import collections
import typing as t


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

        result = self.r.xread({stream_name: last_id}, block=block)
        # result looks like this
        # [
        #   [
        #     b'stream_name', [
        #       (b'1615142762573-0', {b'key': b'val'}),
        #       (b'1615142830679-0', {b'key': b'val2'})]
        #   ]
        # ]
        # we're only reading from one stream, the outer array is of length 1

        ts_item_tuples = next(
            (
                stream_items
                for result_stream_name, stream_items in result
                if result_stream_name == stream_name
            ),
            None,
        )
        # ts_item_tuples looks like
        #   [(b'1615142762573-0', {b'key': b'val'}),
        #    (b'1615142830679-0', {b'key': b'val2'})]
        if ts_item_tuples is None or ts_item_tuples == []:
            return None

        self.stream_pointers[stream_name] = [
            ts for ts, item in ts_item_tuples
        ][-1]
        items = [item for ts, item in ts_item_tuples]
        return items


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
