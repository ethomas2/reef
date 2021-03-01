import random
import typing as t
import t2048._types as types
import itertools


def init_game() -> types.GameState:

    board = [
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
    ]

    choices = list(itertools.product(range(4), range(4)))
    init_placements = random.sample(choices, k=2)
    for (r, c) in init_placements:
        board[r][c] = random.choice([2, 4])
    return types.GameState(player="player", board=board)


def get_indexes(row=None, col=None, rev=False):
    assert (row is None or col is None) and not (row is None and col is None)
    if row is not None and not rev:
        return [(row, c) for c in range(4)]
    elif row is not None and rev:
        return [(row, c) for c in reversed(range(4))]
    elif col is not None and not rev:
        return [(r, col) for r in range(4)]
    elif col is not None and rev:
        return [(r, col) for r in reversed(range(4))]
    else:
        assert False, "bibbidy"


def take_action_mut(gamestate, action):
    if gamestate.player == "player":
        return take_player_action(gamestate, action)
    elif gamestate.player == "environment":
        return take_environment_action(gamestate, action)


def take_environment_action(gamestate, action: types.EnvironmentAction):
    assert gamestate.player == "environment"
    r, c = action.placement
    val = action.val
    gamestate.board[r][c] = val
    gamestate.player = "player"
    return gamestate


def take_player_action(
    gamestate: types.GameState, player_action: types.PlayerAction
):
    assert gamestate.player == "player"
    board = gamestate.board
    action = player_action.action
    if action == "left":
        index_set = [get_indexes(row=r) for r in range(len(board))]
    elif action == "right":
        index_set = [get_indexes(row=r, rev=True) for r in range(len(board))]
    elif action == "up":
        index_set = [
            get_indexes(col=c, rev=False) for c in range(len(board[0]))
        ]
    elif action == "down":
        index_set = [
            get_indexes(col=c, rev=True) for c in range(len(board[0]))
        ]
    else:
        assert False, f"action {action} is not left or right or up or down"

    for indexes in index_set:
        fixed = [False, False, False, False]
        for counter in range(1000):
            idx_and_coord_to_fill = next(
                (
                    (idx_to_fill, (r, c))
                    for (idx_to_fill, (r, c)) in enumerate(indexes[:-1])
                    if board[r][c] is None or not fixed[idx_to_fill]
                ),
                None,
            )
            if idx_and_coord_to_fill is None:
                break
            coord_to_move = next(
                (
                    (r, c)
                    for (r, c) in indexes[idx_and_coord_to_fill[0] + 1 :]
                    if board[r][c] is not None
                ),
                None,
            )
            if coord_to_move is None:
                break

            (i1, (r1, c1)) = idx_and_coord_to_fill
            (r2, c2) = coord_to_move

            if board[r1][c1] is None:
                board[r1][c1] = board[r2][c2]
                board[r2][c2] = None
            elif board[r1][c1] is not None and board[r2][c2] == board[r1][c1]:
                # merge
                board[r1][c1] = 2 * board[r1][c1]
                fixed[i1] = True
                board[r2][c2] = None
                # print("\tmerge", row)
            else:  # just move idx_to_move over
                (r3, c3) = indexes[i1 + 1]
                tmp = board[r2][c2]
                board[r2][c2] = None
                board[r3][c3] = tmp
                fixed[i1] = True
                # print("\tmove over", row)

        if counter == 1000:
            raise Exception("oh no")
    gamestate.player = "environment"
    return gamestate


def is_over(state: types.GameState) -> t.Optional[t.Union[types.Player]]:
    if get_all_actions(state) == []:
        return "player"


BREAKPOINT = 4096  # assume score will not be over 4192


def get_final_score(state: types.GameState) -> t.Dict[str, float]:
    board = state.board
    score = sum([x for row in board for x in row if x is not None])

    assert score <= BREAKPOINT
    normalized_score = score / BREAKPOINT
    return {"player": normalized_score}


def rollout_policy(gamestate: types.GameState) -> t.Dict[str, float]:
    board = gamestate.board
    score = sum([x for row in board for x in row if x is not None])

    coords = itertools.product(range(4), range(4))

    def is_peak(i, j):
        neighbors = [
            (x, y)
            for x, y in [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
            if 0 <= x < 4 and 0 <= y < 4
        ]
        return all(
            (board[i][j] or 0) > (board[i2][j2] or 0) for i2, j2 in neighbors
        )

    peaks = [board[i][j] for (i, j) in coords if is_peak(i, j)]
    non_max_peaks = sorted(peaks)[1:]
    score -= sum(non_max_peaks)

    assert score <= BREAKPOINT
    normalized_score = score / BREAKPOINT
    return {"player": normalized_score}


def get_all_actions(gamestate: types.GameState) -> t.List[types.Action]:
    if gamestate.player == "player":
        return get_all_player_actions(gamestate)
    elif gamestate.player == "environment":
        return get_all_environment_actions(gamestate)
    else:
        assert False, 'gamestate.player must be "player" or "environment"'


def get_all_player_actions(
    gamestate: types.GameState,
) -> t.List[types.PlayerAction]:
    board = gamestate.board
    actions = set()
    locations = itertools.product(range(4), range(4))
    for (r, c) in locations:
        if r + 1 < 4 and (
            board[r + 1][c] is None or board[r + 1][c] == board[r][c]
        ):
            actions.add("down")
        elif r - 1 >= 0 and (
            board[r - 1][c] is None or board[r - 1][c] == board[r][c]
        ):
            actions.add("up")
        elif c + 1 < 4 and (
            board[r][c + 1] is None or board[r][c + 1] == board[r][c]
        ):
            actions.add("right")
        elif c - 1 >= 0 and (
            board[r][c - 1] is None or board[r][c - 1] == board[r][c]
        ):
            actions.add("left")
    return [types.PlayerAction(action=a) for a in actions]


def get_all_environment_actions(
    gamestate: types.GameState,
) -> t.List[types.EnvironmentAction]:
    assert gamestate.player == "environment"
    board = gamestate.board
    indicies = itertools.product(range(4), range(4))
    placements = [(r, c) for r, c in indicies if board[r][c] is None]
    return [
        types.EnvironmentAction(placement=placement, val=val)
        for placement in placements
        for val in [1, 2]
    ]


def get_random_action(gamestate: types.GameState) -> t.Optional[types.Action]:
    if gamestate.player == "environment":
        board = gamestate.board
        indicies = itertools.product(range(4), range(4))
        placements = [(r, c) for r, c in indicies if board[r][c] is None]
        return types.EnvironmentAction(
            placement=random.choice(placements), val=random.choice([2, 4])
        )
    else:
        return random.choice(get_all_actions(gamestate))


def encode_action(action: types.Action) -> str:
    if isinstance(action, types.PlayerAction):
        return f"player action: {action.action}"
    elif isinstance(action, types.EnvironmentAction):
        return f"environment action: {action.placement} {action.val}"
    else:
        assert False, f"Unexpected action type {action}"


def get_players():
    return ["player"]
