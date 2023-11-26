import json
import textwrap
import itertools
import io

import utils
from reef import _types as types


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

    return buffer.getvalue().strip()


def hconcat_with_delim(*items: str, delim=" "):
    assert len(items) > 0
    max_item_height = max([len(item.split("\n")) for item in items])
    spacer = f"{delim}\n" * max_item_height

    def arr_join(arr, sep):
        it = iter(arr)
        yield next(it)
        for x in it:
            yield sep
            yield x

    return hconcat(*arr_join(items, spacer))


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
    if isinstance(card.card_face, types.HighestSurround):
        c, s = (
            COLOR_TO_LETTER[card.card_face.center].upper(),
            COLOR_TO_LETTER[card.card_face.surrounder].lower(),
        )
        icon = textwrap.dedent(
            f"""
            {s}{s}{s}
            {s}{c}{s}
            {s}{s}{s}
            """
        ).strip()
        title = "HighestSurround"
    elif isinstance(card.card_face, types.Square):
        c = COLOR_TO_LETTER[card.card_face.color]
        icon = textwrap.dedent(
            f"""
            {c}{c}
            {c}{c}
            """
        ).strip()
        title = "Square"
    elif isinstance(card.card_face, types.Stack):
        c = COLOR_TO_LETTER[card.card_face.color]
        h = card.card_face.height
        icon = textwrap.dedent(
            f"""
            {c}{h}
            """
        ).strip()
        title = "Stack"
    elif isinstance(card.card_face, types.ThreeDiag):
        c = COLOR_TO_LETTER[card.card_face.color]
        icon = textwrap.dedent(
            f"""
            {c}
             {c}
              {c}
            """
        ).strip()
        title = "ThreeDiag"
    elif isinstance(card.card_face, types.ThreeL):
        c = COLOR_TO_LETTER[card.card_face.color]
        icon = textwrap.dedent(
            f"""
            {c}
            {c}{c}
            """
        ).strip()
        title = "ThreeL"
    elif isinstance(card.card_face, types.ThreeOrthog):
        c = COLOR_TO_LETTER[card.card_face.color]
        icon = f"{c}{c}{c}"
        title = "ThreeOrthog"
    elif isinstance(card.card_face, types.TwoDiag):
        c1 = COLOR_TO_LETTER[card.card_face.stack1.color]
        c2 = COLOR_TO_LETTER[card.card_face.stack2.color]
        h1 = card.card_face.stack1.height
        h2 = card.card_face.stack2.height

        icon = textwrap.dedent(
            f"""
            {c1}{h1}
                {c2}{h2}
            """
        ).strip()
        title = "TwoDiag"
    elif isinstance(card.card_face, types.TwoOrthog):
        c1 = COLOR_TO_LETTER[card.card_face.stack1.color]
        c2 = COLOR_TO_LETTER[card.card_face.stack2.color]
        h1 = card.card_face.stack1.height
        h2 = card.card_face.stack2.height
        icon = f"{c1}{h1} {c2}{h2}"
        title = "TwoOrthog"
    else:
        utils.assert_never(f"Invalid icon type {type(card.card_face)}")

    c1, c2 = COLOR_TO_LETTER[card.color1], COLOR_TO_LETTER[card.color2]
    card_text = "\n".join([title, icon, f"{c1} {c2}"])
    return card_text


def format_hand(hand: types.Hand) -> str:
    if len(hand) == 0:
        return ""
    return hconcat_with_delim(*map(format_card, hand), delim="  ")


def format_center(center: types.Center):
    if len(center) == 0:
        return ""
    cards = [format_card(card) + "\n" + str(score) for card, score in center]
    return hconcat_with_delim(*cards, delim="  ")


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

    center = format_center(gamestate.center)
    leftcol = "\n".join(
        [
            f"Player: {gamestate.player}, decksize: {len(gamestate.deck)}",
            f"Score player 0 : {gamestate.players[0].score}",
            format_hand(hand1),
            format_board(board1),
            hconcat(
                "-" * ((80 - len(center)) // 2),
                center,
                "-" * ((80 - len(center)) // 2),
            ),
            "",
            f"Score player 1: {gamestate.players[1].score}",
            format_board(board2),
            format_hand(hand2),
        ]
    )

    rightcol = json.dumps(gamestate.color_piles, indent=2)
    return hconcat(leftcol, rightcol)
