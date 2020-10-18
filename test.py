import random

import utils
import _types as types


def test_pprint_board():
    def random_boardstack():
        i = random.randint(0, 4)
        if i == 0:
            return types.BoardStack(height=i, color=None)
        return types.BoardStack(
            height=i, color=random.choice(list(types.Color))
        )

    board = [[random_boardstack() for _x in range(4)] for _y in range(4)]
    utils.pprint_board(board)
