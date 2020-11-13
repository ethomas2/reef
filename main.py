import argparse
import random
import subprocess
import sys

import typing as t

from engine import get_action
from rules import init_game, take_action, is_over, get_all_actions
import fmt
import utils


def play_human_vs_human():
    nplayers = 2
    gamestate = init_game(nplayers)
    while True:
        subprocess.call("clear")
        print(fmt.format_gamestate(gamestate))
        print("\n")
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
):
    if seed:
        random.seed(seed)
    nplayers = 2
    gamestate = init_game(nplayers)
    n_turns_skipped_in_a_row = 0
    while True:
        if output:
            print(fmt.format_gamestate(gamestate), file=output)
            print("\n", file=output)
        if is_over(gamestate):
            break

        actions = get_all_actions(gamestate)

        # hack to get around the no valid actions problem
        if len(actions) == 0:
            print(f"NO ACTIONS for player {gamestate.turn}. SKIPPING")
            n_turns_skipped_in_a_row += 1
            if n_turns_skipped_in_a_row == nplayers:
                break
            else:
                continue
        else:
            n_turns_skipped_in_a_row = 0

        action = random.choice(actions)
        newgamestate = take_action(gamestate, action)
        assert (
            newgamestate is not None
        ), "get_all_actions() returned invalid action"
        gamestate = newgamestate

    if output:
        print("Game Over", file=output)


if __name__ == "__main__":
    # file, seed

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--file",
        default="-",
        type=str,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
    )

    args = vars(parser.parse_args())
    filepath, seed = args.get("file"), args.get("seed")
    if filepath is None:
        utils.assert_never(
            "Argparse did not force user to provide --file argument"
        )

    if filepath == "-":
        play_random_computer_vs_random_computer(seed=seed, output=sys.stdout)
    else:
        with open(filepath, "w+") as f:
            play_random_computer_vs_random_computer(seed=seed, output=f)
