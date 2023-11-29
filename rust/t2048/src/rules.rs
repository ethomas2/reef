use rand::prelude::*;
use rand::seq::SliceRandom;

const SIDE: usize = 4;
const BOARD_SIZE: usize = SIDE * SIDE;

type SpaceValue = usize;
// TODO: consider making this a u8 where x represents 2**x
type Board = [SpaceValue; BOARD_SIZE];

enum Player {
    Player,
    Environment,
}

pub struct GameState(Board, Player);

enum PlayerAction {
    Up,
    Down,
    Left,
    Right,
}

struct EnvironmentAction {
    placement: (u8, u8),
    val: SpaceValue,
}

pub fn init_game() -> GameState {
    let mut rng = rand::thread_rng(); // Create a random number generator
    let (loc1, loc2) = (0..BOARD_SIZE)
        .flat_map(|i| ((i + 1)..BOARD_SIZE).map(move |j| (i, j)))
        .choose(&mut rng)
        .unwrap();
    let mut gs: GameState = GameState(Default::default(), Player::Player);
    gs.0[loc1] = *[2, 4].choose(&mut rng).unwrap();
    gs.0[loc2] = *[2, 4].choose(&mut rng).unwrap();

    gs
}
