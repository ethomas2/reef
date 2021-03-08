import typing as t

from dataclasses import dataclass


G = t.TypeVar("G")
A = t.TypeVar("A")
P = t.TypeVar("P")


@dataclass
class Rules(t.Generic[G, A, P]):
    init_game: t.Callable[[], G]
    take_action_mut: t.Callable[[G, A], G]
    is_over: t.Callable[[G], t.Optional[P]]
    get_final_score: t.Callable[[G], t.Dict[str, float]]
    encode_action: t.Callable[[A], str]
    decode_action: t.Callable[[str], A]
    get_random_action: t.Callable[[G], t.Optional[A]]
    get_all_actions: t.Callable[[G], t.List[A]]
    get_players: t.Callable[[G], t.List[P]]

    format_gamestate: t.Callable[[G], str]

    encode_gamestate: t.Callable[[G], bytes]
    decode_gamestate: t.Callable[[bytes], G]


def load_rules(game_type: str):
    if game_type == "2048":
        import t2048.rules as rules
        import t2048.fmt as fmt
    elif game_type == "connect4":
        import connect4.rules as rules
        import connect4.fmt as fmt
    else:
        raise Exception(f"Unknown game type {game_type}")

    return Rules(
        init_game=rules.init_game,
        take_action_mut=rules.take_action_mut,
        is_over=rules.is_over,
        get_final_score=rules.get_final_score,
        encode_action=rules.encode_action,
        decode_action=rules.decode_action,
        get_random_action=rules.get_random_action,
        get_all_actions=rules.get_all_actions,
        get_players=rules.get_players,
        format_gamestate=fmt.format_gamestate,
        encode_gamestate=rules.encode_gamestate,
        decode_gamestate=rules.decode_gamestate,
    )
