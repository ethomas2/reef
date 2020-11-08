import sys
import random
import subprocess

import typing as t

from engine import get_action
from rules import init_game, take_action, is_over, get_all_actions
import fmt


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


def play_random_computer_vs_random_computer(
    seed: t.Optional[int] = None,
    output: t.Optional[t.IO] = None,
    clear_terminal: bool = False,
):
    if seed:
        random.seed(seed)
    nplayers = 2
    gamestate = init_game(nplayers)
    while True:
        if output:
            if clear_terminal:
                subprocess.call("clear")
            print(fmt.format_gamestate(gamestate), file=output)
            if is_over(gamestate):
                print("Game Over", file=output)
                break
            print("\n", file=output)

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
    play_random_computer_vs_random_computer(
        seed=0, output=sys.stdout, clear_terminal=True
    )
