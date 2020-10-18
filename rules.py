import itertools
import random
import copy
import typing as t

import _types as types
from utils import assert_never


def init_game() -> types.GameState:
    nplayers = 2
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
        types.Player(
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
            c: (
                20
                if nplayers <= 2
                else 30
                if nplayers == 3
                else 35
                if nplayers == 4
                else assert_never(f"Invalid Number of Players {nplayers}")
            )
            for c in [
                types.Color.red,
                types.Color.yellow,
                types.Color.purple,
                types.Color.green,
            ]
        },
    )

    if gamestate.color_piles is None:
        raise Exception("invalid number of players")

    return gamestate


def get_actions_for_player(
    state: types.GameState, player_idx: int
) -> t.List[types.Action]:
    draw_actions = [
        types.DrawCardAction(i, card)
        for i, (card, coins) in enumerate(state.center)
        if len(state.players[player_idx].hand) < 3
    ]

    player = state.players[player_idx]
    board = player.board
    play_actions = [
        types.PlayCardAction(
            hand_index=hand_index,
            card=card,
            placement1=(x1, y1, board[x1][y1].height + 1),
            placement2=(x2, y2, board[x2][y2].height + 1),
        )
        for hand_index, card in enumerate(player.hand)
        for (x1, y1) in itertools.product(range(4), repeat=2)
        for (x2, y2) in itertools.product(range(4), repeat=2)
        if (x1, y1) != (x2, y2)
    ]
    play_actions.extend(
        [
            types.PlayCardAction(
                hand_index=hand_index,
                card=card,
                placement1=(x, y, board[x][y].height + p1),
                placement2=(x, y, board[x][y].height + p2),
            )
            for hand_index, card in enumerate(player.hand)
            for (x, y) in itertools.product(range(4), repeat=2)
            for p1, p2 in [[1, 2], [2, 1]]
        ]
    )
    play_actions = [
        pa
        for pa in play_actions
        if pa.placement1[2] <= 4 and pa.placement2[2] <= 4
    ]

    actions = t.cast(t.List[types.Action], draw_actions) + t.cast(
        t.List[types.Action], play_actions
    )
    return actions


def _is_valid(state: types.GameState) -> bool:
    """
    will be used eventually to make sure get_actions_for_player only returns
    valid actions. For debugging only.
    """
    # - For each player they don't have any board stacks with length > 4
    # - Each hand is <= 4

    return True


def takeaction(
    old_state: types.GameState, player_idx: int, action: types.Action
) -> types.GameState:
    new_state = copy.deepcopy(old_state)
    player = new_state.players[player_idx]
    if isinstance(action, types.DrawCardAction):
        (drawn_card, score) = new_state.center.pop(action.center_index)
        player.hand.append(drawn_card)
        player.score += score
    elif isinstance(action, types.PlayCardAction):
        new_state
    assert _is_valid(new_state)
    return new_state
