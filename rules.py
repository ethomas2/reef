import itertools
import random
import copy
import typing as t

import _types as types
from utils import assert_never


def init_game(nplayers: int) -> types.GameState:
    deck = types.ALL_CARDS[:]
    random.shuffle(deck)
    empty_stack = types.BoardStack(height=0, color=None)
    empty_board = [
        [empty_stack, empty_stack, empty_stack, empty_stack],
        [empty_stack, empty_stack, empty_stack, empty_stack],
        [empty_stack, empty_stack, empty_stack, empty_stack],
        [empty_stack, empty_stack, empty_stack, empty_stack],
    ]
    players = [
        types.PlayerState(
            hand=[deck.pop(), deck.pop()],
            board=copy.deepcopy(empty_board),
            score=0,
        )
        for _ in range(nplayers)
    ]
    gamestate = types.GameState(
        players=players,
        history=[],
        center=[
            (deck.pop(), 0),
            (deck.pop(), 0),
            (deck.pop(), 0),
            (deck.pop(), 0),
        ],
        deck=deck,
        color_piles={
            color: (
                20
                if nplayers <= 2
                else 30
                if nplayers == 3
                else 35
                if nplayers == 4
                else assert_never(f"Invalid Number of Players {nplayers}")
            )
            for color in [
                types.Color.red,
                types.Color.yellow,
                types.Color.purple,
                types.Color.green,
            ]
        },
    )

    return gamestate


# def get_actions_for_player(
#     state: types.GameState, player_idx: int
# ) -> t.List[types.Action]:
#     draw_actions: t.List[types.Action] = [
#         types.DrawCenterCardAction(i)
#         for i in range(len(state.center))
#         if len(state.players[player_idx].hand) < 3
#     ]
#     draw_actions.append(types.DrawDeckAction())

#     player = state.players[player_idx]
#     play_actions = [
#         types.PlayCardAction(
#             hand_index=hand_index,
#             placement1=(x1, y1),
#             placement2=(x2, y2),
#         )
#         for hand_index in range(len(player.hand))
#         for (x1, y1) in itertools.product(range(4), repeat=2)
#         for (x2, y2) in itertools.product(range(4), repeat=2)
#     ]
#     play_actions.extend(
#         [
#             types.PlayCardAction(
#                 hand_index=hand_index,
#                 placement1=(x, y),
#                 placement2=(x, y),
#             )
#             for hand_index in range(len(player.hand))
#             for (x, y) in itertools.product(range(4), repeat=2)
#             for p1, p2 in [[1, 2], [2, 1]]
#         ]
#     )
#     play_actions = [
#         pa
#         for pa in play_actions
#         if pa.placement1[2] <= 4 and pa.placement2[2] <= 4
#     ]

#     actions = t.cast(t.List[types.Action], draw_actions) + t.cast(
#         t.List[types.Action], play_actions
#     )
#     return actions


def _is_gamestate_valid(state: types.GameState) -> bool:
    """
    will be used eventually to make sure get_actions_for_player only returns
    valid actions. For debugging only.
    """

    boardstacks_are_less_than_4 = all(
        (
            stack.height <= 4
            for player in state.players
            for boardrow in player.board
            for stack in boardrow
        )
    )

    hands_are_less_than_4 = all(
        (len(player.hand) <= 4 for player in state.players)
    )

    color_piles_are_non_negative = all(
        pile >= 0 for pile in state.color_piles.values()
    )

    return (
        boardstacks_are_less_than_4
        and hands_are_less_than_4
        and color_piles_are_non_negative
    )


def take_action(
    old_state: types.GameState, action: types.Action, player_idx: int
) -> t.Optional[types.GameState]:
    """ Returns new gamestate, or None if action was invalid """
    new_state = copy.deepcopy(old_state)
    player = new_state.players[player_idx]
    if isinstance(action, types.DrawCenterCardAction):
        if len(new_state.center) == 0:
            return None
        (drawn_card, score) = new_state.center.pop(action.center_index)
        player.hand.append(drawn_card)
        player.score += score
    elif isinstance(action, types.PlayCardAction):
        card = player.hand.pop(action.hand_index)
        x1, y1 = action.placement1
        x2, y2 = action.placement2
        player.board[x1][y1] = types.BoardStack(
            player.board[x1][y1].height + 1,
            card.color1,
        )
        player.board[x2][y2] = types.BoardStack(
            player.board[x2][y2].height + 1,
            card.color2,
        )
        new_state.color_piles[card.color1] -= 1
        new_state.color_piles[card.color2] -= 1

        player.score += score_action(old_state, new_state, action)
    elif isinstance(action, types.DrawDeckAction):
        card = new_state.deck.pop()
        player.hand.append(card)

    if not _is_gamestate_valid(new_state):
        return None
    return new_state


def score_action(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
) -> int:
    return 1
