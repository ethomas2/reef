import itertools
from dataclasses import dataclass
import contextlib
import argparse
import random
import sys

# from connect4.heuristic import heuristic
import utils


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play 2048")
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
    )

    parser.add_argument("player_type", type=str, choices=AGENT_TYPES)

    args = vars(parser.parse_args())
    filepath, nofile, seed, player_type = (
        args.get("file"),
        args.get("no_file"),
        args.get("seed"),
        args.get("player_type"),
    )

    if seed is not None:
        random.seed(seed)

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

        agent = get_agent(player_type)

        play_game(agent, output)
