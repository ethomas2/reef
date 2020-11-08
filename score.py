import typing as t
import itertools

import _types as types
import utils


def score_play_action(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
) -> int:
    player = old_state.players[old_state.turn]
    card_played = player.hand[action.hand_index]
    if isinstance(card_played.card_face, types.HighestSurround):
        return score_highest_surround(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.Square):
        return score_square(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.Stack):
        return score_stack(old_state, new_state, action, card_played.card_face)
    elif isinstance(card_played.card_face, types.ThreeDiag):
        return score_three_diag(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.ThreeL):
        return score_three_L(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.ThreeOrthog):
        return score_three_orthog(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.TwoDiag):
        return score_two_diag(
            old_state, new_state, action, card_played.card_face
        )
    elif isinstance(card_played.card_face, types.TwoOrthog):
        return score_two_orthog(
            old_state, new_state, action, card_played.card_face
        )
    else:
        utils.assert_never(f"unknown card face {type(card_played.card_face)}")


T = t.TypeVar("T")

ALL_COORDS = list(itertools.product(range(4), range(4)))


def height_match(real_height: int, card_height: t.Union[int, str]):
    if isinstance(card_height, int):
        return real_height == card_height
    else:
        assert len(card_height) == 2 and card_height[1] == "+"
        return int(card_height[0]) == real_height


def score_highest_surround(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.HighestSurround,
) -> int:
    player = new_state.players[old_state.turn]
    board = player.board

    center_color = card_face.center

    highest_height_of_center_color = max(
        (
            board[x][y].height
            for (x, y) in ALL_COORDS
            if board[x][y] is not None and board[x][y].color == center_color
        ),
        default=None,
    )
    if highest_height_of_center_color is None:
        # There is no placement of center color
        return 0
    highest_positions_of_center_color = [
        (x, y)
        for (x, y) in ALL_COORDS
        if board[x][y]
        and board[x][y].color == center_color
        and board[x][y].height == highest_height_of_center_color
    ]

    def possible_scores():
        for (x, y) in highest_positions_of_center_color:
            yield sum(
                1
                for i, j in itertools.product([-1, 0, 1], [-1, 0, 1])
                if 0 <= x + i < 4 and 0 <= y + j < 4
                # shouldn't be necessary bc center is always differnt color
                # than surrounder
                and (i, j) != (0, 0)
                and board[x + i][y + j] == card_face.surrounder
            )

    return max(possible_scores())


def score_square(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.Square,
) -> int:
    """
    Form a graph where each node represents a square (represented by it's top
    left corner) and an edge exists between two nodes if the two squares
    overlap (i.e. the top left coords of the squares are too close together).
    Return the size of the maximal covering. (See maximal_covering for details)
    """
    card = old_state.players[old_state.turn].hand[action.hand_index]
    block_top_left_coords = list(itertools.product(range(3), range(3)))
    exclusion_edges = [
        ((x1, y1), (x2, y2))
        for ((x1, y1), (x2, y2)) in itertools.combinations(
            block_top_left_coords, 2
        )
        if abs(x1 - x2) < 2 or abs(y1 - y2) < 2
    ]
    return card.victory_points * len(
        maximal_covering(block_top_left_coords, exclusion_edges)
    )


def score_stack(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.Stack,
) -> int:
    board = new_state.players[old_state.turn].board

    return sum(
        1
        for row in board
        for stack in row
        if stack.color == card_face.color
        and height_match(stack.height, card_face.height)
    )


def score_three_diag(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.ThreeDiag,
) -> int:
    card = old_state.players[old_state.turn].hand[action.hand_index]
    top_left_coords = itertools.product(range(2), range(4))
    directions = [(1, 1), (1, -1)]
    diags = [
        ((x, y), (dx, dy))
        for (x, y), (dx, dy) in itertools.product(top_left_coords, directions)
        if 0 <= x + 2 * dx < 4 and 0 <= y + 2 * dy < 4
    ]
    exclusion_edges = [
        (d1, d2)
        for d1, d2 in itertools.combinations(diags, 2)
        if (set(d1) & set(d2))
    ]

    return card.victory_points * len(maximal_covering(diags, exclusion_edges))


def score_three_L(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.ThreeL,
) -> int:
    card = old_state.players[old_state.turn].hand[action.hand_index]
    new_board = new_state.players[old_state.turn].board

    blocks = []
    for (x, y) in ALL_COORDS:
        if new_board[x][y] == card_face.color:
            possible_blocks = [
                [(x, y), (x + 1, y), (x, y + 1)],
                [(x, y), (x + 1, y), (x, y - 1)],
                [(x, y), (x - 1, y), (x, y + 1)],
                [(x, y), (x - 1, y), (x, y - 1)],
            ]
            possible_blocks = [
                [
                    (x, y)
                    for (x, y) in possible_block
                    if 0 <= x < 4 and 0 <= y < 4
                ]
                for possible_block in possible_blocks
            ]
            possible_blocks = [
                possible_block
                for possible_block in possible_blocks
                if all(
                    new_board[x][y] == card_face.color
                    for (x, y) in possible_block
                )
            ]
            blocks.extend(possible_blocks)

    exclusion_edges = [
        (b1, b2)
        for b1, b2 in itertools.combinations(blocks, 2)
        if (set(b1) & set(b2))
    ]

    return card.victory_points * len(maximal_covering(blocks, exclusion_edges))


def score_three_orthog(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.ThreeOrthog,
) -> int:
    card = old_state.players[old_state.turn].hand[action.hand_index]
    new_board = new_state.players[old_state.turn].board

    blocks = []
    for (x, y) in ALL_COORDS:
        if new_board[x][y] == card_face.color:
            possible_blocks = [
                [(x, y), (x + 1, y), (x + 2, y)],
                [(x, y), (x, y + 1), (x, y + 2)],
            ]
            possible_blocks = [
                [
                    (x, y)
                    for (x, y) in possible_block
                    if 0 <= x < 4 and 0 <= y < 4
                ]
                for possible_block in possible_blocks
            ]
            possible_blocks = [
                possible_block
                for possible_block in possible_blocks
                if all(
                    new_board[x][y] == card_face.color
                    for (x, y) in possible_block
                )
            ]
            blocks.extend(possible_blocks)

    exclusion_edges = [
        (b1, b2)
        for b1, b2 in itertools.combinations(blocks, 2)
        if (set(b1) & set(b2))
    ]

    return card.victory_points * len(maximal_covering(blocks, exclusion_edges))


def score_two_diag(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.TwoDiag,
) -> int:
    card = old_state.players[old_state.turn].hand[action.hand_index]
    new_board = new_state.players[old_state.turn].board

    blocks = []
    for (x, y) in ALL_COORDS:
        if (
            new_board[x][y]
            and new_board[x][y].color == card_face.stack1.color
            and height_match(new_board[x][y].height, card_face.stack1.height)
        ):
            possible_blocks = [
                [(x, y), (x + 1, y + 1)],
                [(x, y), (x + 1, y - 1)],
                [(x, y), (x - 1, y + 1)],
                [(x, y), (x - 1, y - 1)],
            ]
            possible_blocks = [
                [
                    (x, y)
                    for (x, y) in possible_block
                    if 0 <= x < 4 and 0 <= y < 4
                ]
                for possible_block in possible_blocks
            ]
            possible_blocks = [
                [s1, (x2, y2)]  # square1 and square2
                for [s1, (x2, y2)] in possible_blocks
                if new_board[x2][y2]  # useful for if change to be optional
                and new_board[x2][y2].color == card_face.stack2.color
                and height_match(
                    new_board[x2][y2].height, card_face.stack2.height
                )
            ]
            blocks.extend(possible_blocks)

    exclusion_edges = [
        (b1, b2)
        for b1, b2 in itertools.combinations(blocks, 2)
        if (set(b1) & set(b2))
    ]
    return card.victory_points * len(maximal_covering(blocks, exclusion_edges))


def score_two_orthog(
    old_state: types.GameState,
    new_state: types.GameState,
    action: types.PlayCardAction,
    card_face: types.TwoOrthog,
) -> int:
    card = old_state.players[old_state.turn].hand[action.hand_index]
    new_board = new_state.players[old_state.turn].board

    blocks = []
    for (x, y) in ALL_COORDS:
        if (
            new_board[x][y]
            and new_board[x][y].color == card_face.stack1.color
            and height_match(new_board[x][y].height, card_face.stack1.height)
        ):
            possible_blocks = [
                [(x, y), (x + 1, y)],
                [(x, y), (x - 1, y)],
                [(x, y), (x, y + 1)],
                [(x, y), (x, y - 1)],
            ]
            possible_blocks = [
                [
                    (x, y)
                    for (x, y) in possible_block
                    if 0 <= x < 4 and 0 <= y < 4
                ]
                for possible_block in possible_blocks
            ]
            possible_blocks = [
                [s1, (x2, y2)]  # square1 and square2
                for [s1, (x2, y2)] in possible_blocks
                if new_board[x2][y2]
                and new_board[x2][y2].color == card_face.stack2.color
                and height_match(
                    new_board[x2][y2].height, card_face.stack2.height
                )
            ]
            blocks.extend(possible_blocks)

    exclusion_edges = [
        (b1, b2)
        for b1, b2 in itertools.combinations(blocks, 2)
        if (set(b1) & set(b2))
    ]
    return card.victory_points * len(maximal_covering(blocks, exclusion_edges))


def maximal_covering(
    nodes: t.List[T], edges: t.List[t.Tuple[T, T]]
) -> t.List[T]:
    """
    Given a list of nodes and edges, return the maximum number of nodes you can
    such that no two nodes share an edge
    """
    if len(nodes) <= 1:
        return nodes

    n0 = nodes[0]

    # covering1. Include n0.
    nodes_that_dont_touch_n0 = [
        u
        for u in nodes
        if u != n0 and (n0, u) not in edges and (u, n0) not in edges
    ]
    covering1 = [nodes[0]] + maximal_covering(nodes_that_dont_touch_n0, edges)

    # covering2. Do not include n0
    covering2 = maximal_covering(nodes[:1], edges)

    if len(covering1) > len(covering2):
        return covering1
    return covering2
