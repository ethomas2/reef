import typing as t

from connect4.rules import BOARD_HEIGHT, BOARD_LENGTH, other_player
import connect4._types as types
import utils

ALL_COORDS = [(r, c) for r in range(BOARD_HEIGHT) for c in range(BOARD_LENGTH)]


def compute_triples():
    horizontal_triples = [
        [(r, c), (r, c + 1), (r, c + 2)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH - 2)
    ]
    vertical_triples = [
        [(r, c), (r + 1, c), (r + 2, c)]
        for c in range(BOARD_LENGTH)
        for r in range(BOARD_HEIGHT - 2)
    ]
    diag_triples1 = [
        [(r, c), (r + 1, c + 1), (r + 2, c + 2)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH)
        if r + 2 < BOARD_HEIGHT and c + 2 < BOARD_LENGTH
    ]
    diag_triples2 = [
        [(r, c), (r + 1, c - 1), (r + 2, c - 2)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH)
        if r + 2 < BOARD_HEIGHT and c - 2 >= 0
    ]
    return (
        horizontal_triples + vertical_triples + diag_triples1 + diag_triples2
    )


def compute_quads():
    horizontal_triples = [
        [(r, c), (r, c + 1), (r, c + 2), (r, c + 3)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH - 3)
    ]
    vertical_triples = [
        [(r, c), (r + 1, c), (r + 2, c), (r + 3, c)]
        for c in range(BOARD_LENGTH)
        for r in range(BOARD_HEIGHT - 3)
    ]
    diag_triples1 = [
        [(r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH)
        if r + 3 < BOARD_HEIGHT and c + 3 < BOARD_LENGTH
    ]
    diag_triples2 = [
        [(r, c), (r + 1, c - 1), (r + 2, c - 2), (r + 3, c - 3)]
        for r in range(BOARD_HEIGHT)
        for c in range(BOARD_LENGTH)
        if r + 3 < BOARD_HEIGHT and c - 3 >= 0
    ]
    return (
        horizontal_triples + vertical_triples + diag_triples1 + diag_triples2
    )


ALL_TRIPLES = compute_triples()
ALL_QUADS = compute_quads()


def heuristic(gamestate: types.GameState) -> float:

    this_player = gamestate.turn
    opponent = other_player(this_player)
    board = gamestate.board

    ############################ Count open quads ###########################
    open_quads_this_player = set()
    open_quads_opponent = set()
    for quad in ALL_QUADS:
        singleton: t.Optional[t.Tuple[int, int]] = None
        num_nones = 0
        num_this_player = 0
        num_opponent = 0
        for (r, c) in quad:
            val = board[r][c]
            if val is None:
                num_nones += 1
                singleton = (r, c)
            elif val == this_player:
                num_this_player += 1
            elif val == opponent:
                num_opponent += 1
            else:
                raise Exception(f"unexpected value in board {val}")

        if num_nones == 1 and num_this_player == 3 and num_opponent == 0:
            open_quads_this_player.add(singleton)
        elif num_nones == 1 and num_this_player == 1 and num_opponent == 3:
            open_quads_opponent.add(singleton)

    if open_quads_this_player:
        return float("+inf")  # can win this turn
    elif len(open_quads_opponent) > 1:
        return float("-inf")  # can't stop opponent from winning

    ############################ Count open trips ###########################
    open_trips_this_player = set()
    open_trips_opponent = set()
    for trip in ALL_TRIPLES:
        singleton = None  # t.Optional[t.Tuple[int, int]]
        num_nones = 0
        num_this_player = 0
        num_opponent = 0
        for (r, c) in trip:
            val = board[r][c]

            if val is None:
                num_nones += 1
                singleton = (r, c)
            elif val == this_player:
                num_this_player += 1
            elif val == opponent:
                num_opponent += 1
            else:
                raise Exception(f"unexpected value in board {val}")

        if num_nones == 1 and num_this_player == 3 and num_opponent == 0:
            open_trips_this_player.add(singleton)
        elif num_nones == 1 and num_this_player == 1 and num_opponent == 3:
            open_trips_opponent.add(singleton)

    num_open_trips = len(open_trips_this_player) - len(open_trips_opponent)

    # see https://www.youtube.com/watch?v=YqqcNjQMX18&ab_channel=KeithGalli
    my_parity = (
        1
        if gamestate.turn == "X"
        else 0
        if gamestate.turn == "O"
        else utils.assert_never(f"Unexpected player {gamestate.turn}")
    )
    open_quads_on_my_parity = [
        1 for x in open_quads_this_player if (x[0] % 2) == my_parity
    ]
    open_quads_on_opponet_parity = [
        1 for x in open_quads_this_player if (x[0] % 2) == my_parity
    ]
    open_quads_on_my_parity = [
        (r, c)
        for (r, c) in open_quads_on_my_parity
        if not any(
            (r2, c) not in open_quads_on_opponet_parity
            for r2 in range(BOARD_HEIGHT - 1, r, -1)
        )
    ]
    open_quads_on_opponet_parity = [
        (r, c)
        for (r, c) in open_quads_on_opponet_parity
        if not any(
            (r2, c) not in open_quads_on_my_parity
            for r2 in range(BOARD_HEIGHT - 1, r, -1)
        )
    ]

    middle_bias = (
        sum(
            (3 - abs(3 - c))
            for (r, c) in ALL_COORDS
            if board[r][c] == this_player
        )
        / 3.0
    )
    return (
        num_open_trips
        + middle_bias
        + len(open_quads_on_my_parity)
        - len(open_quads_on_opponet_parity)
    )
