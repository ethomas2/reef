import itertools

import utils
from rules import init_game, take_action
from engine import get_action


def play_human_vs_human():
    nplayers = 2
    gamestate = init_game(nplayers)
    for player_idx in itertools.repeat(*range(nplayers)):
        print(utils.format_gamestate(gamestate))
        while True:
            action = get_action(player_idx, gamestate)
            newgamestate = take_action(gamestate, action, player_idx)
            if newgamestate is not None:
                break
        utils.pprint(newgamestate)
        if is_over(newgamestate):
            print("Game Over")
            break
        gamestate = newgamestate


if __name__ == "__main__":
    play_human_vs_human()
