import random
import sys
import contextlib
import argparse
import typing as t

import redis

from client.agent import Agent, AGENT_TYPES, get_agent
import common.main as common
import utils


def play_game(
    agents: t.List[Agent], game_type: str, output: t.Optional[t.IO] = None
):

    # TODO: generalze this so you can have more than one agent
    agent = agents[0]

    rules = common.load_rules(game_type)
    gamestate = rules.init_game()

    while True:
        # print gamestate
        if output:
            print(rules.format_gamestate(gamestate), file=output)
            print("\n", file=output)
        if rules.is_over(gamestate) is not None:
            score = rules.get_final_score(gamestate)
            if output:
                print(f"Game Over. Score: {score}", file=output)
            break

        # progress gamestate
        if gamestate.player == "environment":
            random_action = rules.get_random_action(gamestate)
            if random_action is None:
                utils.assert_never(
                    "Random action is None even though game is not over"
                )
            else:
                rules.take_action_mut(gamestate, random_action)
        else:
            if agent.agent_type == "human":
                while True:
                    action = agent.get_action(gamestate)
                    newgamestate = rules.take_action_mut(gamestate, action)
                    if newgamestate is None:
                        print("Invalid action")
                    else:
                        break
            else:
                action = agent.get_action(gamestate)
                if output:
                    print(action, file=output)
                newgamestate = rules.take_action_mut(gamestate, action)
                if newgamestate is None:
                    utils.assert_never(
                        f"Non human agent returned an invalid action {action}"
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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

    parser.add_argument("game_type", type=str, choices=["2048", "connect4"])
    parser.add_argument(
        "player_type", type=str, choices=AGENT_TYPES, nargs="+"
    )

    args = vars(parser.parse_args())
    filepath, nofile, seed, player_types, game_type = (
        args.get("file"),
        args.get("no_file"),
        args.get("seed"),
        args.get("player_type"),
        args.get("game_type"),
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

        default_config = {
            "mcts_budget": 2,
            "n_engine_servers": 2,
        }
        agents = [
            get_agent(player_type, game_type, **default_config)
            for player_type in player_types
        ]

        play_game(agents, game_type, output)
