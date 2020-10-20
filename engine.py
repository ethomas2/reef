"""
Responsible for communication with outside world
"""

import typing as t

import _types as types
import textwrap
import utils


def get_action(player_idx: int, gamestate: types.GameState) -> types.Action:
    print(f"Player {player_idx}")
    action = int(
        utils.get_and_validate_input(
            textwrap.dedent(
                """
           1. Draw card from center
           2. Draw card from deck
           3. Play card
           """
            ),
            lambda n: 1 <= int(n) <= 3,
        )
    )

    if action == 1:
        # draw card from center
        center_size = len(gamestate.center)
        subaction = int(
            utils.get_and_validate_input(
                "Which Card: ", lambda n: 0 <= int(n) < center_size
            )
        )
        return types.DrawCenterCardAction(center_index=subaction)
    elif action == 2:
        # draw card from deck
        return types.DrawDeckAction()
    elif action == 3:
        # play card
        handsize = len(gamestate.players[player_idx].hand)
        hand_index = int(
            utils.get_and_validate_input(
                "Which Card: ", lambda n: 0 <= int(n) < handsize
            )
        )

        def transform(inp: str) -> t.Tuple[int, int]:
            a, b = [int(s.strip()) for s in inp.split(",")]
            return a, b

        placement1 = utils.get_and_transform_input("Placement 1: ", transform)
        placement2 = utils.get_and_transform_input("Placement 2: ", transform)
        return types.PlayCardAction(
            hand_index=hand_index,
            placement1=placement1,
            placement2=placement2,
        )
    else:
        utils.assert_never(f"Invalid action {action}")
