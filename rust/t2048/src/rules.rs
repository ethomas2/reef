use rand::prelude::*;
use rand::seq::SliceRandom;

const SIDE: usize = 4;
const BOARD_SIZE: usize = SIDE * SIDE;

type SpaceValue = usize;

// TODO: consider making this a u8 where x represents 2**x
#[derive(Default)]
struct Board([SpaceValue; BOARD_SIZE]);

impl Board {
    fn get_mut<T>(&mut self, placement: T) -> &mut SpaceValue
    where
        T: Into<Placement>,
    {
        let Placement(r, c) = placement.into();
        // TODO: this cast is ugly. Is this cannonical?
        // https://stackoverflow.com/questions/28273169/how-do-i-convert-between-numeric-types-safely-and-idiomatically
        &mut self.0[(4 * r + c) as usize]
    }
}

enum Player {
    Player,
    Environment,
}

pub struct GameState {
    board: Board,
    player: Player,
}

enum PlayerAction {
    Up,
    Down,
    Left,
    Right,
}

struct Placement(u8, u8); // space on the baord
impl From<usize> for Placement {
    fn from(x: usize) -> Self {
        Self(
            (x / SIDE).try_into().unwrap(),
            (x % SIDE).try_into().unwrap(),
        )
    }
}

struct EnvironmentAction {
    placement: Placement,
    val: SpaceValue,
}

/// union type over PlayerAction and EnvironmentAction
enum Action {
    PlayerAction(PlayerAction),
    EnvironmentAction(EnvironmentAction),
}

pub fn init_game() -> GameState {
    let mut rng = rand::thread_rng(); // Create a random number generator
    let (loc1, loc2) = (0..BOARD_SIZE)
        .flat_map(|i| ((i + 1)..BOARD_SIZE).map(move |j| (i, j)))
        .choose(&mut rng)
        .unwrap();
    let mut gs: GameState = GameState {
        board: Default::default(),
        player: Player::Player,
    };
    *gs.board.get_mut(loc1) = *[2, 4].choose(&mut rng).unwrap();
    *gs.board.get_mut(loc2) = *[2, 4].choose(&mut rng).unwrap();

    gs
}

pub fn take_action_mut(mut gamestate: GameState, action: Action) {
    // TODO: replace this debug assert with is_legal_move(gamestate, action)
    debug_assert!(
        {
            match gamestate.player {
                Player::Player => matches!(action, Action::PlayerAction(..)),
                Player::Environment => matches!(action, Action::EnvironmentAction(..)),
            }
        },
        "illegal move"
    );
    match action {
        Action::PlayerAction(player_action) => take_player_action_mut(gamestate, player_action),
        Action::EnvironmentAction(environment_action) => {
            take_environment_action_mut(gamestate, environment_action)
        }
    }
}

fn take_environment_action_mut(mut gamestate: GameState, action: EnvironmentAction) {
    debug_assert!(matches!(gamestate.player, Player::Environment));
    let EnvironmentAction { placement, val } = action;
    *gamestate.board.get_mut(placement) = val;
    gamestate.player = Player::Player;
}

fn take_player_action_mut(gamestate: GameState, action: PlayerAction) {}
