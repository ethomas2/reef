import itertools
import subprocess

import utils
from rules import init_game, take_action, is_over
from engine import get_action


def play_human_vs_human():
    nplayers = 2
    gamestate = init_game(nplayers)
    for player_idx in itertools.cycle(range(nplayers)):
        subprocess.call("clear")
        print(utils.format_gamestate(gamestate))
        if is_over(gamestate):
            print("Game Over")
            break

        while True:
            action = get_action(player_idx, gamestate)
            newgamestate = take_action(gamestate, action, player_idx)
            if newgamestate is None:
                print("Invalid Action")
                continue
            break

        gamestate = newgamestate


if __name__ == "__main__":
    play_human_vs_human()
