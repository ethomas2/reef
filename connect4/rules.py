import random
import typing as t

from connect4 import _types as types
import utils


BOARD_LENGTH = 7
BOARD_HEIGHT = 6


def init_game() -> types.GameState:
    return types.GameState(
        board=[[None] * BOARD_LENGTH for _ in range(BOARD_HEIGHT)],
        num_moves=0,
        turn="X",
    )


def take_action_mut(
    gamestate: types.GameState, action: types.Action
) -> t.Optional[types.GameState]:

    board = gamestate.board
    col, mark = action

    next_available_row = next(
        (i for i in range(BOARD_HEIGHT - 1, -1, -1) if board[i][col] is None),
        None,
    )

    if next_available_row is None:
        return None

    board[next_available_row][col] = mark
    gamestate.num_moves += 1
    gamestate.turn = (
        "X"
        if gamestate.turn == "O"
        else "O"
        if gamestate.turn == "X"
        else utils.assert_never(f"Unknown board turn {gamestate.turn}")
    )
    return gamestate


def is_over(state: types.GameState) -> bool:

    # draw
    if state.num_moves == BOARD_LENGTH * BOARD_HEIGHT:
        return True

    board = state.board
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_LENGTH):
            if board[r][c] is None:
                continue

            # check all to the right
            if c + 3 < BOARD_LENGTH and all(
                board[r][c] == board[x][y]
                for (x, y) in [(r, c), (r, c + 1), (r, c + 2), (r, c + 3)]
            ):
                return True

            # check all down
            if r + 3 < BOARD_HEIGHT and all(
                board[r][c] == board[x][y]
                for (x, y) in [(r, c), (r + 1, c), (r + 2, c), (r + 3, c)]
            ):
                return True

            # check diag down+right
            if (
                r + 3 < BOARD_HEIGHT
                and c + 3 < BOARD_LENGTH
                and all(
                    board[r][c] == board[x][y]
                    for (x, y) in [
                        (r, c),
                        (r + 1, c + 1),
                        (r + 2, c + 2),
                        (r + 3, c + 3),
                    ]
                )
            ):
                return True

            # check diag down+left
            if (
                r + 3 < BOARD_HEIGHT
                and c - 3 >= 0
                and all(
                    board[r][c] == board[x][y]
                    for (x, y) in [
                        (r, c),
                        (r + 1, c - 1),
                        (r + 2, c - 2),
                        (r + 3, c - 3),
                    ]
                )
            ):
                return True

    return False


def get_random_action(gamestate: types.GameState) -> t.Optional[types.Action]:
    turn = gamestate.turn
    board = gamestate.board
    possible_actions = [
        (i, turn) for i in range(BOARD_LENGTH) if board[0][i] is None
    ]
    if len(possible_actions) == 0:
        return None
    return random.choice(possible_actions)
