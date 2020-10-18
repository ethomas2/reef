import itertools

import utils
from rules import init_game
import _types as types


def play_human_vs_random_computer():
    nplayers = 2
    gamestate = init_game(nplayers)
    for player in itertools.repeat(*range(nplayers)):
        while True:
            action = get_action(player, gamestate)
            newgamestate = take_action(gamestate, action)
            if newgamestate is not None:
                break
        utils.pprint(newgamestate)
        if is_over(newgamestate):
            print("Game Over")
            break
        gamestate = newgamestate


if __name__ == "__main__":
    # play_human_vs_random_computer()

    def random_boardstack():
        import random

        i = random.randint(0, 4)
        if i == 0:
            return types.BoardStack(height=i, color=None)
        return types.BoardStack(
            height=i, color=random.choice(list(types.Color))
        )

    board = [[random_boardstack() for _x in range(4)] for _y in range(4)]
    utils.pprint_board(board)
