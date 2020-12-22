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
        raise Exception(f"cannot take action {action} on current board")

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


Draw = t.Literal["draw"]


def is_over(state: types.GameState) -> t.Optional[t.Union[types.Player, Draw]]:

    # draw
    if state.num_moves == BOARD_LENGTH * BOARD_HEIGHT:
        return "draw"

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
                return board[r][c]

            # check all down
            if r + 3 < BOARD_HEIGHT and all(
                board[r][c] == board[x][y]
                for (x, y) in [(r, c), (r + 1, c), (r + 2, c), (r + 3, c)]
            ):
                return board[r][c]

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
                return board[r][c]

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
                return board[r][c]

    return None


def other_player(player: types.Player) -> types.Player:
    return (
        "X"
        if player == "O"
        else "O"
        if player == "X"
        else utils.assert_never(f"Unexpected player {player}")
    )


def undo_action(gamestate: types.GameState, action: types.Action):
    gamestate.turn = other_player(gamestate.turn)
    gamestate.num_moves -= 1
    board = gamestate.board

    c, _ = action
    r = next((i for i in range(BOARD_HEIGHT) if board[i][c] is not None), None)
    assert (
        r is not None
    ), "Tried to undo action for a column which does not have a marker in it"
    board[r][c] = None


def get_all_actions(gamestate: types.GameState) -> t.List[types.Action]:
    turn = gamestate.turn
    board = gamestate.board
    actions = [(i, turn) for i in range(BOARD_LENGTH) if board[0][i] is None]
    return actions


def get_random_action(gamestate: types.GameState) -> t.Optional[types.Action]:
    actions = get_all_actions(gamestate)
    if len(actions) == 0:
        return None
    return random.choice(actions)
