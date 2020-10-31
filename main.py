import random
import subprocess

import fmt
from rules import init_game, take_action, is_over, get_all_actions
from engine import get_action


def play_human_vs_human():
    nplayers = 2
    gamestate = init_game(nplayers)
    while True:
        subprocess.call("clear")
        print(fmt.format_gamestate(gamestate))
        if is_over(gamestate):
            print("Game Over")
            break

        while True:
            action = get_action(gamestate.turn, gamestate)
            newgamestate = take_action(gamestate, action)
            if newgamestate is None:
                print("Invalid Action")
                continue
            break

        gamestate = newgamestate


def play_random_computer_vs_random_computer():
    random.seed(0)
    nplayers = 2
    gamestate = init_game(nplayers)
    while True:
        subprocess.call("clear")
        print(fmt.format_gamestate(gamestate))
        if is_over(gamestate):
            print("Game Over")
            break

        actions = get_all_actions(gamestate)
        assert (
            len(actions) > 0
        ), "player has no actions even though game is not over"
        action = random.choice(actions)
        newgamestate = take_action(gamestate, action)
        assert (
            newgamestate is not None
        ), "get_all_actions() returned invalid action"
        gamestate = newgamestate


if __name__ == "__main__":
    play_random_computer_vs_random_computer()
