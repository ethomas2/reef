import itertools
from dataclasses import dataclass
import contextlib
import argparse
import random
import sys

import typing as t

from t2048.rules import (
    init_game,
    take_action_mut,
    is_over,
    get_random_action,
    get_all_actions,
    final_score,
)

# from connect4.heuristic import heuristic
from t2048 import fmt
import utils
import engine.typesv1 as types
from engine.mctsv1 import mcts_v1
import connect4._types as c4types
from engine.minimax import minimax


AGENT_TYPES = [
    "random",
    "mcts",
    "human",
]

AgentType = t.Union[
    t.Literal["random"],
    t.Literal["mcts"],
    t.Literal["human"],
]


@dataclass
class Agent:
    agent_type: AgentType
    get_action: t.Callable[[c4types.GameState], c4types.Action]


def play_game(agent: Agent, output: t.Optional[t.IO] = None):
    gamestate = init_game()

    while True:
        # print gamestate
        if output:
            print(fmt.format_gamestate(gamestate), file=output)
            print("\n", file=output)
        if is_over(gamestate) is not None:
            score = final_score(gamestate)
            if output:
                print(f"Game Over. Score: {score}", file=output)
            break

        # progress gamestate
        if gamestate.player == "environment":
            random_action = get_random_action(gamestate)
            if random_action is None:
                utils.assert_never(
                    "Random action is None even though game is not over"
                )
            else:
                take_action_mut(gamestate, random_action)
        else:
            if agent.agent_type == "human":
                while True:
                    action = agent.get_action(gamestate)
                    newgamestate = take_action_mut(gamestate, action)
                    if newgamestate is None:
                        print("Invalid action")
                    else:
                        break
            else:
                action = agent.get_action(gamestate)
                if output:
                    print(action, file=output)
                newgamestate = take_action_mut(gamestate, action)
                if newgamestate is None:
                    utils.assert_never(
                        f"Non human agent returned an invalid action {action}"
                    )


def get_agent(agent_type: AgentType) -> Agent:
    if agent_type == "random":

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            random_action = get_random_action(gamestate)
            if random_action is None:
                utils.assert_never(
                    "Random action is None even though game is not over"
                )
            return random_action

        return Agent(
            agent_type=agent_type,
            get_action=get_action,
        )

    elif agent_type == "human":

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            while True:
                inp = input(f"Choose direction (w,a,s,d): ").strip().lower()

                INP_MAP = {"w": "up", "a": "left", "s": "down", "d": "right"}
                if inp not in INP_MAP.keys():
                    print(f"Input must be one of {INP_MAP}")
                    continue

                return INP_MAP[inp]

        return Agent(get_action=get_action, agent_type=agent_type)

    else:
        utils.assert_never(f"Invalid agent type {agent_type}")


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
