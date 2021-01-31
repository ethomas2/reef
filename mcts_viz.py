import connect4._types as c4types
import engine.typesv1 as eng_types
from engine.mctsv1 import mcts_v1
from connect4.rules import (
    # init_game,
    take_action_mut,
    is_over,
    # get_random_action,
    undo_action,
    get_all_actions,
    # other_player,
)


def foo():
    # win on col 2 for X. It's X's turn
    board1 = [
        ["-", "-", "-", "-", "-", "-", "-"],
        ["-", "-", "-", "-", "-", "-", "-"],
        ["-", "-", "-", "X", "-", "-", "-"],
        ["-", "X", "-", "O", "-", "-", "X"],
        ["O", "X", "O", "X", "O", "O", "O"],
        ["X", "O", "X", "X", "O", "O", "X"],
    ]

    # must block on 1
    board2 = [
        ["-", "-", "-", "-", "-", "-", "-"],
        ["-", "-", "-", "-", "-", "-", "-"],
        ["-", "-", "-", "O", "-", "-", "-"],
        ["-", "-", "O", "X", "-", "-", "-"],
        ["-", "-", "X", "O", "-", "-", "-"],
        ["O", "X", "X", "X", "O", "-", "-"],
    ]

    board = board1

    board = [[(x if x != "-" else None) for x in row] for row in board]

    # nx = sum([1 for row in board for x in row if x == "X"])
    # no = sum([1 for row in board for x in row if x == "O"])
    # print(nx, no)

    config = eng_types.MctsConfig(
        take_action_mut=take_action_mut,
        undo_action=undo_action,
        get_all_actions=get_all_actions,
        is_over=is_over,
        players=["X", "O"],
    )
    gamestate = c4types.GameState(
        board=board,
        turn="X",
        num_moves=18,
    )

    print(mcts_v1(config, gamestate))


board = [
    ["-", "-", "-", "O", "O", "-", "X"],
    ["-", "X", "-", "O", "O", "-", "O"],
    ["-", "O", "-", "O", "O", "-", "X"],
    ["-", "O", "O", "X", "X", "-", "O"],
    ["-", "X", "X", "O", "X", "-", "X"],
    ["X", "O", "X", "X", "O", "X", "X"],
]
board = [[(x if x != "-" else None) for x in row] for row in board]

gamestate = c4types.GameState(
    board=board,
    turn="X",
    num_moves=50,
)
print(is_over(gamestate))
