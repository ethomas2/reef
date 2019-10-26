import itertools
import random
import copy

import _types as types


def init_game() -> types.GameState:
    nplayers = 4
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
            board=copy.deepcopy(empty_board)
        )
        for _ in range(nplayers)
    ]
    return types.GameState(
        players=players,
        history=[],
        center=[deck.pop(), deck.pop(), deck.pop(), deck.pop()],
        deck=deck,
    )


def get_actions_for_player(
        state: types.GameState, player_idx: int) -> types.Action:
    draw_actions = [
        types.DrawCardAction(i, card)
        for i, card in enumerate(state.center)
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
    play_actions.extend([
        types.PlayCardAction(
            hand_index=hand_index,
            card=card,
            placement1=(x, y, board[x][y].height + p1),
            placement2=(x, y, board[x][y].height + p2),
        )
        for hand_index, card in enumerate(player.hand)
        for (x, y) in itertools.product(range(4), repeat=2)
        for p1, p2 in [[1, 2], [2, 1]]
    ])
    play_actions = [
        pa
        for pa in play_actions
        if pa.placement1[2] <= 4 and pa.placement2[2] <= 4
    ]

    actions = draw_actions + play_actions
    return actions
