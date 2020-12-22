import typing as t

from connect4.rules import BOARD_HEIGHT, BOARD_LENGTH, other_player
import connect4._types as types


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
        for tup in quad:
            r, c = tup
            val = board[r][c]
            if val is None:
                num_nones += 1
                singleton = tup
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
        for tup in trip:
            r, c = tup
            try:
                val = board[r][c]
            except:
                import pdb

                pdb.set_trace()  # noqa: E702
            if val is None:
                num_nones += 1
                singleton = tup
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

    # not including open quads in the final count because either you have 1
    # open quad, in which case opponent must deal with the threat, or you have
    # 2 in which case you win
    return len(open_trips_this_player) - len(open_trips_opponent)
