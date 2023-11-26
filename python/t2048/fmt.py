import t2048._types as types


def format_gamestate(gamestate: types.GameState):
    board = gamestate.board

    def pad_elm(x):
        n = len(str(x))
        return " " * (4 - n) + str(x)

    padded_nums = [[pad_elm(x) for x in row] for row in board]
    return f"Player: {gamestate.player}\n" + "\n".join(
        ["|".join(row) for row in padded_nums]
    )
