import engine.typesv1 as types
import typing as t

import utils

G = t.TypeVar("G")
A = t.TypeVar("A")
P = t.TypeVar("P")


def minimax(
    config: types.MinimaxConfig[G, A, P], gamestate: G, depth=3
) -> t.Tuple[float, t.Optional[A]]:
    this_player = config.get_player(gamestate)
    opponent = config.other_player(this_player)
    if isinstance(config.action, types.MutableActionConfig):
        take_action_mut, undo_action = (
            config.action.take_action_mut,
            config.action.undo_action,
        )
    elif isinstance(config.action, types.ImmutableActionConfig):
        raise NotImplementedError(
            "minimax not implemented for immutable action config"
        )
    else:
        utils.assert_never(f"Unknown action config type {type(config.action)}")

    get_all_actions, is_over, heuristic = (
        config.get_all_actions,
        config.is_over,
        config.heuristic,
    )
    if (winner := is_over(gamestate)) is not None:
        value = (
            float("+inf")
            if winner == this_player
            else float("-inf")
            if winner == opponent
            else 0  # draw
        )
        return value, None
    if depth == 0:
        return heuristic(gamestate), None

    actions = get_all_actions(gamestate)
    assert actions, "No actions for a non-terminal gamestate"

    action_value_pairs: t.List[t.Tuple[float, A]] = []

    for action in actions:
        newgamestate = take_action_mut(gamestate, action)
        assert newgamestate is not None, (
            "get_all_actions(G) returned"
            "action A for which take_action_mut(G, A) is None"
        )
        value, _ = minimax(config, newgamestate, depth - 1)
        action_value_pairs.append((-1 * value, action))
        undo_action(
            gamestate, action
        )  # restore gamestate since you mutated it

    value, action = max(action_value_pairs)
    return value, action
