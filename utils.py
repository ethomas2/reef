import textwrap
import itertools
import io
import typing as t

import _types as types


def assert_never(msg: str) -> t.NoReturn:
    raise Exception(msg)


T = t.TypeVar("T")


def get_and_validate_input(
    msg: str, validate: t.Callable[[str], t.Any]
) -> str:
    while True:
        inp = input(msg)
        try:
            if not validate(inp):
                continue
            return inp
        except Exception:
            continue


def get_and_transform_input(msg: str, transform: t.Callable[[str], T]) -> T:
    while True:
        inp = input(msg)
        try:
            return transform(inp)
        except Exception:
            continue


def hconcat(*schunks: str) -> str:
    buffer = io.StringIO()

    achunks = [chunk.split("\n") for chunk in schunks]
    max_hlength_per_chunk = [max(map(len, achunk)) for achunk in achunks]

    for lines in itertools.zip_longest(*achunks, fillvalue=""):
        print(
            "".join(
                [
                    line + (" " * (padding - len(line)))
                    for padding, line in zip(max_hlength_per_chunk, lines)
                ]
            ),
            file=buffer,
        )

    return buffer.getvalue()


COLOR_TO_LETTER = {
    types.Color.red: "R",
    types.Color.yellow: "Y",
    types.Color.purple: "P",
    types.Color.green: "G",
    types.Color.rainbow: "*",
}


def format_board(board: types.Board) -> str:
    def board_stack_to_str(bs: types.BoardStack) -> str:
        assert not (
            bool(bs.height == 0) ^ bool(bs.color is None)
        ), f"{bs.height=} {bs.color=}"
        if bs.color is None:
            return "  "
        color_letter = COLOR_TO_LETTER[bs.color]
        return f"{bs.height}{color_letter}"

    sep = "+--+--+--+--+"
    main = f"\n{sep}\n".join(
        [
            "|" + "|".join([board_stack_to_str(bs) for bs in row]) + "|"
            for row in board
        ]
    )

    return sep + "\n" + main + "\n" + sep


def format_card(card: types.Card):
    icon, title = "UNSET", "UNSET"
    if isinstance(card.score_type, types.HighestSurround):
        c, s = (
            COLOR_TO_LETTER[card.score_type.center].upper(),
            COLOR_TO_LETTER[card.score_type.surrounder].lower(),
        )
        icon = textwrap.dedent(
            f"""
            {s}{s}{s}
            {s}{c}{s}
            {s}{s}{s}
            """
        ).strip()
        title = "HighestSurround"
    elif isinstance(card.score_type, types.Square):
        c = COLOR_TO_LETTER[card.score_type.color]
        icon = textwrap.dedent(
            f"""
            {c}{c}
            {c}{c}
            """
        ).strip()
        title = "Square"
    elif isinstance(card.score_type, types.Stack):
        c = COLOR_TO_LETTER[card.score_type.color]
        h = card.score_type.height
        icon = textwrap.dedent(
            f"""
            {c}{h}
            """
        ).strip()
        title = "Stack"
    elif isinstance(card.score_type, types.ThreeDiag):
        c = COLOR_TO_LETTER[card.score_type.color]
        icon = textwrap.dedent(
            f"""
            {c}
             {c}
              {c}
            """
        ).strip()
        title = "ThreeDiag"
    elif isinstance(card.score_type, types.ThreeL):
        c = COLOR_TO_LETTER[card.score_type.color]
        icon = textwrap.dedent(
            f"""
            {c}
            {c}{c}
            """
        ).strip()
        title = "ThreeL"
    elif isinstance(card.score_type, types.ThreeOrthog):
        c = COLOR_TO_LETTER[card.score_type.color]
        icon = f"{c}{c}{c}"
        title = "ThreeOrthog"
    elif isinstance(card.score_type, types.TwoDiag):
        c1 = COLOR_TO_LETTER[card.score_type.stack1.color]
        c2 = COLOR_TO_LETTER[card.score_type.stack2.color]
        h1 = card.score_type.stack1.height
        h2 = card.score_type.stack2.height

        icon = textwrap.dedent(
            f"""
            {c1}{h1}
                {c2}{h2}
            """
        ).strip()
        title = "TwoDiag"
    elif isinstance(card.score_type, types.TwoOrthog):
        c1 = COLOR_TO_LETTER[card.score_type.stack1.color]
        c2 = COLOR_TO_LETTER[card.score_type.stack2.color]
        h1 = card.score_type.stack1.height
        h2 = card.score_type.stack2.height
        icon = f"{c1}{h1} {c2}{h2}"
        title = "TwoOrthog"
    else:
        assert_never(f"Invalid icon type {type(card.score_type)}")

    c1, c2 = COLOR_TO_LETTER[card.color1], COLOR_TO_LETTER[card.color2]
    card_text = "\n".join([title, icon, f"{c1} {c2}"])
    return card_text


def format_hand(hand: types.Hand) -> str:
    formatted_cards = list(map(format_card, hand))
    max_card_height = max([len(card.split("\n")) for card in formatted_cards])
    spacer = " \n" * max_card_height

    def arr_join(arr, sep):
        it = iter(arr)
        yield next(it)
        for x in it:
            yield sep
            yield x

    return hconcat(*arr_join(formatted_cards, spacer))


def format_gamestate(gamestate: types.GameState) -> str:
    nplayers = len(gamestate.players)
    if nplayers != 2:
        raise NotImplementedError(
            f"pprint_gamestate not implemented for {nplayers}"
        )

    hand1, board1, hand2, board2 = (
        gamestate.players[0].hand,
        gamestate.players[0].board,
        gamestate.players[1].hand,
        gamestate.players[1].board,
    )

    return "\n".join(
        [
            format_hand(hand1),
            format_board(board1),
            "-----------------------------------------------------------",
            format_board(board2),
            format_hand(hand2),
        ]
    )
