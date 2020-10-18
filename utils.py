import textwrap
import typing as t

import _types as types


def assert_never(msg: str) -> t.NoReturn:
    raise Exception(msg)


def pprint_board(board: types.Board):
    def board_stack_to_str(bs: types.BoardStack) -> str:
        assert not (
            bool(bs.height == 0) ^ bool(bs.color is None)
        ), f"{bs.height=} {bs.color=}"
        if bs.color is None:
            return "  "
        color_letter = {
            types.Color.red: "R",
            types.Color.yellow: "Y",
            types.Color.purple: "P",
            types.Color.green: "G",
            types.Color.rainbow: "*",
        }[bs.color]
        return f"{bs.height}{color_letter}"

    sep = "+--+--+--+--+"
    print(sep)
    print(
        f"\n{sep}\n".join(
            [
                "|" + "|".join([board_stack_to_str(bs) for bs in row]) + "|"
                for row in board
            ]
        )
    )
    print(sep)


def pprint(gamestate: types.GameState):
    print(
        textwrap.dedent(
            f"""
        +--+--+--+--+
        |  |  |  |  |
        +--+--+--+--+
        |  |  |  |  |
        +--+--+--+--+
        |  |  |  |  |
        +--+--+--+--+
        |  |  |  |  |
        +--+--+--+--+
    """
        )
    )
