import itertools
from dataclasses import dataclass
import contextlib
import argparse
import random
import sys

import typing as t

from connect4.rules import (
    init_game,
    take_action_mut,
    is_over,
    get_final_score,
    get_random_action,
    undo_action,
    get_all_actions,
    other_player,
)
from connect4.heuristic import heuristic
from connect4 import fmt
import utils
import engine.typesv1 as types
from engine.mctsv1 import mcts_v1
import connect4._types as c4types
from engine.minimax import minimax


AGENT_TYPES = [
    "random",
    "minimax",
    "mcts",
    "human",
    "mcts-noh",
    "mcts-previsith",
    "mcts-basich",
]
AgentType = t.Union[
    t.Literal["random"],
    t.Literal["minimax"],
    t.Literal["human"],
    t.Literal["mcts-noh"],
    t.Literal["mcts-previsith"],
    t.Literal["mcts-basich"],
]


@dataclass
class Agent:
    agent_type: AgentType
    get_action: t.Callable[[c4types.GameState], c4types.Action]


def play_game(agent1: Agent, agent2: Agent, output: t.Optional[t.IO] = None):
    gamestate = init_game()
    agents = [agent1, agent2]

    for agent in itertools.cycle(agents):
        if output:
            print(fmt.format_gamestate(gamestate), file=output)
            print("\n", file=output)
        if (winner := is_over(gamestate)) is not None:
            return winner
            if output:
                print(f"Game Over. Winner {winner}", file=output)
            break

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
    mcts_budget = 2
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
    elif agent_type == "minimax":
        config = types.MinimaxConfig(
            action=types.MutableActionConfig(
                take_action_mut=take_action_mut,
                undo_action=undo_action,
            ),
            get_all_actions=get_all_actions,
            is_over=is_over,
            heuristic=heuristic,
            get_player=lambda gs: gs.player,
            other_player=other_player,
        )

        def get_action(gs: c4types.GameState) -> c4types.Action:
            _, action = minimax(config, gs, depth=4)
            return action

        return Agent(
            agent_type=agent_type,
            get_action=get_action,
        )
    elif agent_type == "human":

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            while True:
                inp = input(
                    f"Choose column (0-6) for player {gamestate.player}: "
                )
                try:
                    inp = int(inp)
                except ValueError:
                    print("Input must be an int")
                    continue

                if not 0 <= inp < 7:
                    print("Input must be in range 0-6")
                    continue

                return (inp, gamestate.player)

        return Agent(get_action=get_action, agent_type=agent_type)
    elif agent_type == "mcts-noh":
        config = types.MctsConfig(
            take_action_mut=take_action_mut,
            undo_action=undo_action,
            get_all_actions=get_all_actions,
            is_over=is_over,
            get_final_score=get_final_score,
            players=["X", "O"],
            budget=mcts_budget,
        )

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            return mcts_v1(config, gamestate)

        return Agent(get_action=get_action, agent_type=agent_type)
    elif agent_type == "mcts-basich":
        config = types.MctsConfig(
            take_action_mut=take_action_mut,
            undo_action=undo_action,
            get_all_actions=get_all_actions,
            is_over=is_over,
            get_final_score=get_final_score,
            players=["X", "O"],
            budget=mcts_budget,
            heuristic_type="basic",
            heuristic=heuristic,
        )

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            return mcts_v1(config, gamestate)

        return Agent(get_action=get_action, agent_type=agent_type)

    elif agent_type == "mcts-previsith":
        config = types.MctsConfig(
            take_action_mut=take_action_mut,
            undo_action=undo_action,
            get_all_actions=get_all_actions,
            is_over=is_over,
            get_final_score=get_final_score,
            players=["X", "O"],
            budget=mcts_budget,
            heuristic_type="pre-visit",
            heuristic=heuristic,
        )

        def get_action(gamestate: c4types.GameState) -> c4types.Action:
            return mcts_v1(config, gamestate)

        return Agent(get_action=get_action, agent_type=agent_type)

    else:
        utils.assert_never(f"Invalid agent type {agent_type}")


if __name__ == "__main__":
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
    )

    parser.add_argument("p1", type=str, choices=AGENT_TYPES)
    parser.add_argument("p2", type=str, choices=AGENT_TYPES)

    args = vars(parser.parse_args())
    filepath, nofile, seed, p1_agent_type, p2_agent_type = (
        args.get("file"),
        args.get("no_file"),
        args.get("seed"),
        args.get("p1"),
        args.get("p2"),
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

        p1_agent = get_agent(p1_agent_type)
        p2_agent = get_agent(p2_agent_type)

        play_game(p1_agent, p2_agent, output)
