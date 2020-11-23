import utils
import io

import connect4._types as types


def format_gamestate(gamestate: types.GameState) -> str:
    board = gamestate.board

    buffer = io.StringIO()
    print(f"Turn: {gamestate.turn}\tnum_moves: {gamestate.num_moves}")
    for row in board:
        for x in row:
            ch = (
                "X"
                if x == "X"
                else "O"
                if x == "O"
                else "-"
                if x is None
                else utils.assert_never(f"Unkonwn Space {x}")
            )
            print(ch, end="", file=buffer)
        print("", file=buffer)
    return buffer.getvalue()
