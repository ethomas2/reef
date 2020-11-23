import itertools

# from hypothesis import assume
import hypothesis.strategies as st

from reef.rules import (
    MAX_HAND_SIZE,
    BOARD_SIZE,
    MAX_STACK_HEIGHT,
    # _is_gamestate_valid,
)
from reef import _types as types


@st.composite
def graphs(draw):
    r = draw(st.randoms(use_true_random=False))
    n_nodes = draw(st.integers(min_value=2, max_value=30))
    nodes = list(range(n_nodes))
    # for a graph with n nodes the maximum number of edges is n*(n-1)/2 if
    # every possible edge is chosen
    n_edges = draw(
        st.integers(min_value=0, max_value=int(n_nodes * (n_nodes - 1) / 2))
    )
    all_possible_edges = list(itertools.combinations(nodes, 2))
    edges = r.choices(all_possible_edges, k=n_edges)

    return nodes, edges


def action_strategy():

    placement_strat = st.tuples(
        st.integers(min_value=0, max_value=BOARD_SIZE - 1),
        st.integers(min_value=0, max_value=BOARD_SIZE - 1),
    )
    play_card_strategy = st.builds(
        types.PlayCardAction,
        hand_index=st.integers(min_value=0, max_value=MAX_HAND_SIZE),
        placement1=placement_strat,
        placement2=placement_strat,
    )
    return (
        st.builds(types.DrawCenterCardAction, st.integers(min_value=0))
        | st.builds(types.DrawDeckAction)
        | play_card_strategy
    )


@st.composite
def player_strategy(draw):
    board = []
    for _ in range(4):
        row = []
        for _ in range(4):
            height = draw(st.integers(min_value=0, max_value=MAX_STACK_HEIGHT))
            color = None if height == 0 else draw(st.sampled_from(types.Color))
            row.append(types.BoardStack(height, color))
        board.append(row)

    hand = draw(st.lists(st.builds(types.Card), max_size=MAX_HAND_SIZE))

    return types.PlayerState(
        hand=hand, board=board, score=draw(st.integers(min_value=0))
    )


@st.composite
def gamestate_strategy(draw):
    non_negative_int = st.integers(min_value=0)
    color_piles = st.fixed_dictionaries(
        {k: non_negative_int for k in list(types.Color)}
    )

    gamestate = draw(
        st.builds(
            types.GameState,
            color_piles=color_piles,
            # players hardcoded to 2
            players=st.lists(player_strategy(), min_size=2, max_size=2),
            turn=st.integers(min_value=0, max_value=1),
        )
    )

    # assume(_is_gamestate_valid(gamestate))
    return gamestate
