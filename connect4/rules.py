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
        player="X",
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
    gamestate.player = (
        "X"
        if gamestate.player == "O"
        else "O"
        if gamestate.player == "X"
        else utils.assert_never(f"Unknown board player {gamestate.player}")
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


def get_final_score(state: types.GameState) -> t.Dict[types.Player, float]:
    winner = is_over(state)
    assert winner is not None
    if winner in ["X", "O"]:
        vec = {"X": 0, "O": 0}
        vec[winner] = 1
        return vec
    else:
        return {"X": 0.5, "O": 0.5}


def other_player(player: types.Player) -> types.Player:
    return (
        "X"
        if player == "O"
        else "O"
        if player == "X"
        else utils.assert_never(f"Unexpected player {player}")
    )


def undo_action(gamestate: types.GameState, action: types.Action):
    gamestate.player = other_player(gamestate.player)
    gamestate.num_moves -= 1
    board = gamestate.board

    c, _ = action
    r = next((i for i in range(BOARD_HEIGHT) if board[i][c] is not None), None)
    assert (
        r is not None
    ), "Tried to undo action for a column which does not have a marker in it"
    board[r][c] = None


def get_all_actions(gamestate: types.GameState) -> t.List[types.Action]:
    player = gamestate.player
    board = gamestate.board
    actions = [(i, player) for i in range(BOARD_LENGTH) if board[0][i] is None]
    return actions


def get_random_action(gamestate: types.GameState) -> t.Optional[types.Action]:
    actions = get_all_actions(gamestate)
    if len(actions) == 0:
        return None
    return random.choice(actions)


def encode_action(action: types.Action) -> str:
    raise NotImplementedError
