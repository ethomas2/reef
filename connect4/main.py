import contextlib
import argparse
import random
import sys

import typing as t

from connect4.rules import (
    init_game,
    take_action_mut,
    is_over,
    get_random_action,
)
from connect4 import fmt
import utils


def play_random_computer_vs_random_computer(
    seed: t.Optional[int] = None,
    output: t.Optional[t.IO] = None,
):
    if seed is not None:
        random.seed(seed)
    gamestate = init_game()
    while True:
        if output:
            print(fmt.format_gamestate(gamestate), file=output)
            print("\n", file=output)
        if is_over(gamestate):
            break

        random_action = get_random_action(gamestate)
        if random_action is None:
            utils.assert_never(
                "Random action is None even though game is not over"
            )

        newgamestate = take_action_mut(gamestate, random_action)
        assert (
            newgamestate is not None
        ), "random_action() returned invalid action"

        gamestate = newgamestate

    if output:
        print("Game Over", file=output)


if __name__ == "__main__":
    # file, seed

    parser = argparse.ArgumentParser(description="Process some integers.")
    mut_grp = parser.add_mutually_exclusive_group()
    mut_grp.add_argument(
        "--file",
        default="-",
        type=str,
    )
    mut_grp.add_argument("--no-file", action="store_true")

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
    )

    mut_grp2 = parser.add_mutually_exclusive_group()
    mut_grp2.add_argument(
        "--mcts",
        default=False,
        action="store_true",
    )
    mut_grp2.add_argument(
        "--minimax",
        default=False,
        action="store_true",
    )
    mut_grp2.add_argument(
        "--random",
        default=False,
        action="store_true",
    )

    args = vars(parser.parse_args())
    filepath, nofile, seed, ai_mcts, ai_minimax, ai_random = (
        args.get("file"),
        args.get("no_file"),
        args.get("seed"),
        args.get("mcts"),
        args.get("minimax"),
        args.get("random"),
    )

    with contextlib.ExitStack() as stack:
        if nofile:
            output = None
        elif filepath == "-":
            output = sys.stdout
        elif filepath is not None:
            output = stack.enter_context(open(filepath, "w+"))
        else:
            utils.assert_never(
                "Argparse allowed file=None even though nofile is not given"
            )

        play_random_computer_vs_random_computer(seed=seed, output=output)
