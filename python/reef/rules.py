import itertools
import random
import copy
import typing as t

from reef.score import score_play_action
from utils import assert_never
from reef import _types as types
import utils


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
        player=0,
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
                18
                if nplayers <= 2
                else 24
                if nplayers == 3
                else 28
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


MAX_HAND_SIZE = 4

MAX_STACK_HEIGHT = 4

BOARD_SIZE = 4


def get_all_actions(
    gamestate: types.GameState,
) -> t.List[types.Action]:
    """
    Return all *valid* actions from this gamestate. This method is expensive
    because it calls take_action (which makes a copy of the gamestate). Should
    not be called in simulations
    """

    player_idx = gamestate.player
    player = gamestate.players[player_idx]

    draw_center_actions: t.List[types.Action] = (
        [types.DrawCenterCardAction(i) for i in range(len(gamestate.center))]
        if len(gamestate.players[player_idx].hand) < MAX_HAND_SIZE
        else []
    )

    draw_deck_actions: t.List[types.Action] = (
        [types.DrawDeckAction()]
        if len(gamestate.deck) > 0
        # must play coin to draw from deck. score must be > 0
        and player.score > 0
        else []
    )

    play_card_actions: t.List[types.Action] = [
        types.PlayCardAction(
            hand_index=hand_index,
            placement1=(x1, y1),
            placement2=(x2, y2),
        )
        for hand_index in range(len(player.hand))
        for (x1, y1) in itertools.product(range(4), repeat=2)
        for (x2, y2) in itertools.product(range(4), repeat=2)
    ]

    actions = draw_center_actions + draw_deck_actions + play_card_actions
    valid_actions = [
        action for action in actions if is_valid_action(gamestate, action)
    ]
    return valid_actions


def get_random_action(gamestate: types.GameState) -> t.Optional[types.Action]:

    player_idx = gamestate.player
    player = gamestate.players[player_idx]

    # can you do a draw card action
    possible_action_types: t.List[t.Type[types.Action]] = []
    if gamestate.center != [] and len(player.hand) < MAX_HAND_SIZE:
        possible_action_types.append(types.DrawCenterCardAction)

    # can you do a draw deck action
    if (
        gamestate.deck != []
        and player.score > 0
        and len(player.hand) < MAX_HAND_SIZE
    ):
        possible_action_types.append(types.DrawDeckAction)

    # can you do a play card action
    hand_idx_choices = [
        idx
        for (idx, card) in enumerate(player.hand)
        if (
            card.color1 == card.color2
            and gamestate.color_piles[card.color1] >= 2
        )
        or (
            card.color1 != card.color2
            and gamestate.color_piles[card.color1] >= 1
            and gamestate.color_piles[card.color2] >= 1
        )
    ]

    if player.hand != [] and hand_idx_choices != []:
        # TODO: maybe put a check in here to make sure there's a place to put
        # the card (e.g. haven't filled up the board). Should never occur in a
        # real game bc you'll run out of deck before you fill up the board
        possible_action_types.append(types.PlayCardAction)

    if possible_action_types == []:
        return None

    # Now take an action
    action_type = random.choice(possible_action_types)

    if action_type == types.DrawCenterCardAction:
        return types.DrawCenterCardAction(
            random.randint(0, len(gamestate.center)) - 1
        )
    elif action_type == types.DrawDeckAction:
        return types.DrawDeckAction()
    elif action_type == types.PlayCardAction:
        placement1 = random.choice(
            [
                (x, y)
                for (x, y) in itertools.product(
                    range(BOARD_SIZE), range(BOARD_SIZE)
                )
                if player.board[x][y].height < MAX_STACK_HEIGHT
            ]
        )
        x, y = placement1
        player.board[x][y].height += 1  # kinda a hack
        placement2 = random.choice(
            [
                (x, y)
                for (x, y) in itertools.product(
                    range(BOARD_SIZE), range(BOARD_SIZE)
                )
                if player.board[x][y].height < MAX_STACK_HEIGHT
            ]
        )
        player.board[x][y].height -= 1
        return types.PlayCardAction(
            hand_index=random.choice(hand_idx_choices),
            placement1=placement1,
            placement2=placement2,
        )
    else:
        utils.assert_never("invalid action type in get_random_action")


def is_valid_action(gamestate: types.GameState, action: types.Action) -> bool:
    """
    Returns if this action is valid from this gamestate. Much cheaper than
    checking if take_action(gamestate, action) is None. We validate that
    is_valid_action(G, A) is true iff take_action(G, A) is not None with a
    hypothesis test
    """

    if isinstance(action, types.DrawCenterCardAction):
        player = gamestate.players[gamestate.player]
        if len(gamestate.center) == 0:
            return False
        if len(player.hand) >= MAX_HAND_SIZE:
            return False
        if action.center_index >= len(gamestate.center):
            return False
    elif isinstance(action, types.PlayCardAction):
        player = gamestate.players[gamestate.player]
        board = player.board
        x1, y1 = action.placement1
        x2, y2 = action.placement2

        boardstacks_are_less_than_4 = (
            board[x1][y1].height + 2 <= MAX_STACK_HEIGHT
            if (x1, y1) == (x2, y2)
            else (
                board[x1][y1].height + 1 <= MAX_STACK_HEIGHT
                and board[x2][y2].height + 1 <= MAX_STACK_HEIGHT
            )
        )
        if not boardstacks_are_less_than_4:
            return False

        if action.hand_index >= len(player.hand):
            return False
        card = player.hand[action.hand_index]
        color_piles_are_non_negative = (
            gamestate.color_piles[card.color1] - 2 >= 0
            if card.color1 == card.color2
            else (
                gamestate.color_piles[card.color1] - 1 >= 0
                and gamestate.color_piles[card.color2] - 1 >= 0
            )
        )
        if not color_piles_are_non_negative:
            return False
    elif isinstance(action, types.DrawDeckAction):
        player = gamestate.players[gamestate.player]
        if len(gamestate.deck) == 0:
            return False
        if len(player.hand) >= MAX_HAND_SIZE:
            return False
        if player.score <= 0:
            return False

    return True


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


# TODO: consider making an lru cache out of this so that when you call
# get_all_actions, which calls this to see if valid, when you later call
# take_action the result is already cached
def take_action(
    old_state: types.GameState,
    action: types.Action,
) -> t.Optional[types.GameState]:
    """
    Returns new gamestate, or None if action was invalid. This method is
    expensive because it makes a copy of the gamestate so it doesn't have to
    mutate the gamestate. Should not be called too much in simulations.
    """
    new_state = utils.copy(old_state)
    return take_action_mut(new_state, action)


def take_action_mut(
    state: types.GameState,
    action: types.Action,
) -> t.Optional[types.GameState]:
    player = state.players[state.player]
    if isinstance(action, types.DrawCenterCardAction):
        if action.center_index >= len(state.center):
            return None
        (drawn_card, score) = state.center.pop(action.center_index)
        player.hand.append(drawn_card)
        player.score += score

        if len(state.deck) > 0:
            state.center.append((state.deck.pop(), 0))

    elif isinstance(action, types.PlayCardAction):
        if action.hand_index >= len(player.hand):
            return None
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
        state.color_piles[card.color1] -= 1
        state.color_piles[card.color2] -= 1

        player.score += score_play_action(state, action, card)
    elif isinstance(action, types.DrawDeckAction):
        if len(state.deck) == 0:
            return None
        card = state.deck.pop()

        if len(player.hand) >= MAX_HAND_SIZE:
            return None
        player.hand.append(card)

        # put a coin on an arbitrary center card that has the lowest number of
        # coins on it . TODO: fix it so the player has a choice of what card to
        # put it on
        if player.score == 0:
            return None
        player.score -= 1

        if state.center:
            # if there are cards in the center, add 1 coin to the card with the
            # smallest card stack. In practice there will always be cards in
            # the center. This check only exists so hypothesis tests can make
            # empty centers and not blow up
            idx, card, score = min(
                (
                    (idx, card, score)
                    for (idx, (card, score)) in enumerate(state.center)
                ),
                key=lambda x: x[2],
            )
            state.center[idx] = (card, score + 1)
    else:
        utils.assert_never(f"unknown action type {type(action)}")

    state.player = (state.player + 1) % len(state.players)

    if not _is_gamestate_valid(state):
        return None
    return state


def is_over(gamestate: types.GameState) -> bool:
    return len(gamestate.deck) == 0 or (
        any(pile == 0 for pile in gamestate.color_piles.values())
        and gamestate.player == 0
    )
