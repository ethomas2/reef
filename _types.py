from dataclasses import dataclass
import enum
import typing as t


#################################### Color ####################################


class Color(enum.Enum):
    red = "red"
    yellow = "yellow"
    purple = "purple"
    green = "green"
    rainbow = "rainbow"


red, yellow, purple, green, rainbow = (
    Color.red,
    Color.yellow,
    Color.purple,
    Color.green,
    Color.rainbow,
)


################################# Score types #################################


@dataclass
class HighestSurround:
    center: Color
    surrounder: Color


@dataclass
class Square:
    color: Color


@dataclass
class Stack:
    height: t.Union[int, str]
    color: Color


@dataclass
class ThreeDiag:
    color: Color


@dataclass
class ThreeL:
    color: Color


@dataclass
class ThreeOrthog:
    color: Color


@dataclass
class TwoDiag:
    stack1: Stack
    stack2: Stack


@dataclass
class TwoOrthog:
    stack1: Stack
    stack2: Stack


ScoreType = t.Union[
    HighestSurround,
    Square,
    Stack,
    ThreeDiag,
    ThreeL,
    ThreeOrthog,
    TwoDiag,
    TwoOrthog,
]


@dataclass
class Card:
    color1: Color
    color2: Color
    scrore_type: ScoreType
    victory_points: int


ALL_CARDS = [
    Card(purple, purple, Square(red), 6),
    Card(green, green, Stack(3, yellow), 4),
    Card(red, yellow, Stack(4, purple), 5),
    Card(purple, purple, ThreeDiag(red), 4),
    Card(purple, purple, Stack(3, green), 4),
    Card(yellow, green, Stack(3, rainbow), 2),
    Card(red, red, Stack("1+", green), 1),
    Card(yellow, yellow, Square(green), 6),
    Card(green, green, TwoOrthog(Stack("1+", purple), Stack("1+", yellow)), 3),
    Card(green, green, HighestSurround(purple, yellow), 2),
    Card(red, red, Stack(2, yellow), 2),
    Card(green, green, ThreeL(yellow), 4),
    Card(yellow, yellow, ThreeDiag(green), 4),
    Card(yellow, yellow, Stack("1+", purple), 1),
    Card(yellow, yellow, Stack("1+", purple), 1),
    Card(red, yellow, ThreeOrthog(green), 4),
    Card(green, green, TwoOrthog(Stack(2, purple), Stack(2, purple)), 5),
    Card(purple, purple, ThreeL(green), 4),
    Card(red, red, ThreeL(purple), 4),
    Card(red, red, HighestSurround(yellow, purple), 2),
    Card(purple, purple, Stack("1+", yellow), 1),
    Card(purple, red, Stack(4, rainbow), 3),
    Card(yellow, purple, Stack(4, green), 5),
    Card(red, purple, Stack(2, rainbow), 1),
    Card(green, green, TwoDiag(Stack("2+", purple), Stack("2+", red)), 5),
    Card(purple, purple, TwoOrthog(Stack(2, red), Stack(2, red)), 5),
    Card(green, green, TwoOrthog(Stack("1+", red), Stack("1+", purple)), 3),
    Card(red, red, Square(yellow), 6),
    Card(green, green, Stack(2, purple), 2),
    Card(red, red, Stack(3, purple), 4),
    Card(purple, purple, HighestSurround(red, green), 2),
    Card(yellow, yellow, HighestSurround(green, red), 2),
    Card(green, green, ThreeDiag(purple), 4),
    Card(red, green, ThreeOrthog(purple), 4),
    Card(red, red, HighestSurround(purple, green), 2),
    Card(green, purple, Stack(4, red), 5),
    Card(green, yellow, TwoOrthog(Stack(2, rainbow), Stack(2, rainbow)), 2),
    Card(yellow, yellow, Stack(2, green), 2),
    Card(red, red, TwoDiag(Stack("2+", purple), Stack("2+", yellow)), 5),
    Card(green, green, HighestSurround(yellow, red), 2),
    Card(purple, purple, TwoOrthog(Stack("1+", red), Stack("1+", green)), 3),
    Card(green, green, Stack("1+", red), 1),
    Card(red, red, ThreeDiag(yellow), 4),
    Card(yellow, yellow, TwoOrthog(Stack(2, green), Stack(2, green)), 5),
    Card(purple, purple, TwoDiag(Stack("2+", red), Stack("2+", yellow)), 5),
    Card(yellow, yellow, Stack(3, red), 4),
    Card(yellow, yellow, TwoDiag(Stack("2+", red), Stack("2+", green)), 5),
    Card(red, red, TwoDiag(Stack("2+", yellow), Stack("2+", green)), 5),
    Card(red, red, TwoOrthog(Stack("1+", green), Stack("1+", yellow)), 3),
    Card(yellow, yellow, TwoDiag(Stack("2+", purple), Stack("2+", green)), 5),
    Card(purple, purple, HighestSurround(green, yellow), 2),
    Card(green, green, Square(purple), 6),
    Card(green, purple, ThreeOrthog(yellow), 4),
    Card(purple, purple, Stack(2, red), 2),
    Card(red, red, TwoOrthog(Stack(2, yellow), Stack(2, yellow)), 5),
    Card(yellow, yellow, ThreeL(red), 4),
    Card(red, green, Stack(4, yellow), 5),
    Card(purple, yellow, ThreeOrthog(red), 4),
    Card(yellow, yellow, HighestSurround(red, purple), 2),
    Card(purple, purple, TwoOrthog(Stack("1+", yellow), Stack("1+", red)), 3),
    Card(
        yellow, yellow, TwoOrthog(Stack("1+", purple), Stack("1+", green)), 3
    ),
]


# ------------------------- Other -------------------------
Hand = t.List[Card]


@dataclass
class BoardStack:
    height: int
    color: t.Optional[Color]


Board = t.List[t.List[BoardStack]]


@dataclass
class Player:
    hand: Hand
    board: Board
    score: int


History = t.List[Card]
Center = t.List[t.Tuple[Card, int]]


@dataclass
class GameState:
    players: t.List[Player]
    history: History
    center: Center
    deck: t.List[Card]
    color_piles: t.Dict[Color, int]


@dataclass
class DrawCenterCardAction:
    center_index: int  # TODO: do we need this?
    card: Card


@dataclass
class DrawDeckAction:
    pass


@dataclass
class PlayCardAction:
    hand_index: int  # TODO: do we need this?
    card: Card

    # placement1/placement2 are tuples of x,y,height where we place the tuples.
    # The third index is only necessary if they have the same placement, in
    # which case the third index indicates the height
    placement1: t.Tuple[int, int, int]
    placement2: t.Tuple[int, int, int]


Action = t.Union[DrawCenterCardAction, DrawDeckAction, PlayCardAction]
