use rand::prelude::*;
use rand::seq::SliceRandom;

const SIDE: usize = 4;
const BOARD_SIZE: usize = SIDE * SIDE;

type SpaceValue = usize;

// TODO: consider making this a u8 where x represents 2**x
#[derive(Default, PartialEq, Eq, Debug, Clone)]
struct Board([SpaceValue; BOARD_SIZE]);

impl Board {
    /// This method is kind of extra. Why this dance of converting stuff to a placement?
    fn get_mut<T>(&mut self, placement: T) -> &mut SpaceValue
    where
        T: Into<Placement>,
    {
        let Placement(r, c) = placement.into();
        // TODO: this cast is ugly. Is this cannonical?
        // https://stackoverflow.com/questions/28273169/how-do-i-convert-between-numeric-types-safely-and-idiomatically
        &mut self.0[(4 * r + c) as usize]
    }

    /// Take the given board and "move" everything left. I.e. take the left action. All tiles move
    /// left as far as possible and "squash" with the tile to the left of them if they're the same
    fn move_left(self: &mut Self) -> &mut Self {
        for r in 0..SIDE {
            // left = 0
            // right = first non empty
            // if left is empty, move right tile to left idx
            // else if left and right same -> squash and move left over one
            // else if left and right diff -> move right over and move left to right

            let mut left_idx = 0;
            loop {
                let left_tile = *self.get_mut((r, left_idx));
                let right_idx_opt =
                    ((left_idx + 1)..SIDE).find(|idx| *self.get_mut((r, *idx)) != 0);
                if matches!(right_idx_opt, None) {
                    break;
                }
                let right_idx = right_idx_opt.unwrap();
                let right_tile = *self.get_mut((r, right_idx));

                if left_tile == 0 {
                    // move right tile to left idx
                    *self.get_mut((r, left_idx)) = right_tile;
                    *self.get_mut((r, right_idx)) = 0;

                    // purposely don't increase left_idx. Give this a chance to merge
                } else if left_tile == right_tile {
                    // squash
                    *self.get_mut((r, left_idx)) = 2 * left_tile;
                    *self.get_mut((r, right_idx)) = 0; // empty
                    left_idx += 1;
                } else if left_tile != right_tile {
                    *self.get_mut((r, left_idx + 1)) = right_tile;
                    if right_idx != left_idx + 1 {
                        *self.get_mut((r, right_idx)) = 0; // empty
                    }
                    left_idx += 1;
                } else {
                    unreachable!()
                }
            }
        }
        self
    }

    fn rotate_clockwise(self: &mut Self) -> &mut Self {
        // TODO: get rid of the rotate variable. Extra memory allocation
        // TODO: get rid of this whole thing. Replace rotateions with a view on top of the board
        let mut rotated: Board = Default::default();

        for r in 0..SIDE {
            for c in 0..SIDE {
                let new_r = c;
                let new_c = SIDE - 1 - r;
                *rotated.get_mut((new_r, new_c)) = *self.get_mut((r, c));
            }
        }

        self.0.copy_from_slice(&rotated.0);
        self
    }

    fn rotate_counter_clockwise(self: &mut Self) -> &mut Self {
        // TODO: get rid of the rotate variable. Extra memory allocation
        // TODO: get rid of this whole thing. Replace rotateions with a view on top of the board
        let mut rotated: Board = Default::default();

        for r in 0..SIDE {
            for c in 0..SIDE {
                let new_r = SIDE - 1 - c;
                let new_c = r;
                *rotated.get_mut((new_r, new_c)) = *self.get_mut((r, c));
            }
        }

        self.0.copy_from_slice(&rotated.0);
        self
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

impl From<(usize, usize)> for Placement {
    fn from((r, c): (usize, usize)) -> Self {
        Self(r.try_into().unwrap(), c.try_into().unwrap())
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

fn take_player_action_mut(mut gamestate: GameState, action: PlayerAction) {
    debug_assert!(matches!(gamestate.player, Player::Player));
    let GameState { ref mut board, .. } = gamestate;
    match action {
        PlayerAction::Left => {
            board.move_left();
        }
        PlayerAction::Right => {
            board
                .rotate_clockwise()
                .rotate_clockwise()
                .move_left()
                .rotate_clockwise()
                .rotate_clockwise();
        }
        PlayerAction::Up => {
            board
                .rotate_counter_clockwise()
                .move_left()
                .rotate_clockwise();
        }
        PlayerAction::Down => {
            board
                .rotate_clockwise()
                .move_left()
                .rotate_counter_clockwise();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rotate_clockwise() {
        let mut board: Board = Board([
            1, 2, 3, 4, //
            5, 6, 7, 8, //
            9, 10, 11, 12, //
            13, 14, 15, 16, //
        ]);

        let expected = Board([
            13, 9, 5, 1, //
            14, 10, 6, 2, //
            15, 11, 7, 3, //
            16, 12, 8, 4, //
        ]);

        board.rotate_clockwise();

        assert_eq!(board, expected);
    }

    #[test]
    fn test_rotate_clockwise_and_counter_clockwise_are_opposites() {
        let orig = Board(
            (*(0..16).collect::<Vec<_>>().as_slice())
                .try_into()
                .unwrap(),
        );
        let mut mutated = orig.clone();
        mutated.rotate_counter_clockwise().rotate_clockwise();
        assert_eq!(orig, mutated);
    }

    #[test]
    fn test_move_left_simple() {
        let mut board: Board = Board([
            1, 0, 0, 0, //
            0, 1, 0, 0, //
            0, 0, 1, 0, //
            0, 0, 0, 1, //
        ]);
        board.move_left();

        let expected: Board = Board([
            1, 0, 0, 0, //
            1, 0, 0, 0, //
            1, 0, 0, 0, //
            1, 0, 0, 0, //
        ]);

        assert_eq!(board, expected);
    }

    #[test]
    fn test_move_left_squash() {
        let mut board: Board = Board([
            1, 1, 0, 0, //
            1, 1, 1, 1, //
            1, 2, 0, 2, //
            2, 0, 1, 1, //
        ]);
        board.move_left();

        let expected: Board = Board([
            2, 0, 0, 0, //
            2, 2, 0, 0, //
            1, 4, 0, 0, //
            2, 2, 0, 0, //
        ]);
        assert_eq!(board, expected);
    }
}
