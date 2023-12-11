use itertools::iproduct;
use itertools::Itertools;
use rand::rngs::ThreadRng;
use rand::seq::SliceRandom;
use rand::Rng;
use std::fmt;
use std::fmt::Display;
use std::fmt::Write;
use std::str::FromStr;

const SIDE: usize = 4;
const BOARD_SIZE: usize = SIDE * SIDE;

//////////////////////////////////// types ////////////////////////////////////

// TODO: consider making this a u8 where x represents 2**x
type SpaceValue = usize;

#[derive(Default, PartialEq, Eq, Debug, Clone)]
struct Board([SpaceValue; BOARD_SIZE]);

#[derive(Debug, Copy, Clone)]
pub enum Player {
    Player,
    Environment,
}

#[derive(Debug)]
pub struct GameState {
    board: Board,
    player: Player,
}

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone)]
pub enum PlayerAction {
    Up,
    Down,
    Left,
    Right,
}

#[derive(Debug, Clone)]
struct Placement(u8, u8); // space on the baord

#[derive(Debug, Clone)]
pub struct EnvironmentAction {
    placement: Placement,
    val: SpaceValue,
}

#[derive(Debug)]
pub struct IllegalActionError(Action);

/// union type over PlayerAction and EnvironmentAction
#[derive(Debug, Clone)]
pub enum Action {
    PlayerAction(PlayerAction),
    EnvironmentAction(EnvironmentAction),
}

/////////////////////////////// Implementations ///////////////////////////////
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

impl FromStr for PlayerAction {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.trim() {
            "Up" | "U" | "u" => Ok(PlayerAction::Up),
            "Down" | "D" | "d" => Ok(PlayerAction::Down),
            "Left" | "L" | "l" => Ok(PlayerAction::Left),
            "Right" | "R" | "r" => Ok(PlayerAction::Right),
            _ => Err(format!("Unknown Action {}", s)),
        }
    }
}

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

    fn get<T>(&self, placement: T) -> SpaceValue
    where
        T: Into<Placement>,
    {
        let Placement(r, c) = placement.into();
        // TODO: this cast is ugly. Is this cannonical?
        // https://stackoverflow.com/questions/28273169/how-do-i-convert-between-numeric-types-safely-and-idiomatically
        self.0[(4 * r + c) as usize]
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

impl GameState {
    pub fn to_console(&self) -> Result<String, std::fmt::Error> {
        let mut s = String::new();
        let GameState { board, player } = self;
        // TODO: what to do if writeln! returns an error
        match player {
            Player::Player => writeln!(&mut s, "player :: Player")?,
            Player::Environment => writeln!(&mut s, "player :: Environment")?,
        };
        let printable: Vec<_> = board.0.iter().map(|val| format!("{}", val)).collect();
        let width = printable.iter().map(|s| s.len()).max().unwrap();
        for r in 0..SIDE {
            for c in 0..SIDE {
                write!(
                    &mut s,
                    " {:width$} ",
                    printable[SIDE * r + c],
                    width = width
                )?;
            }
            writeln!(&mut s)?;
        }
        Ok(s)
    }

    pub fn init_game(rng: &mut rand::rngs::ThreadRng) -> GameState {
        let &(loc1, loc2) = (0..BOARD_SIZE)
            .flat_map(|i| ((i + 1)..BOARD_SIZE).map(move |j| (i, j)))
            .collect::<Vec<_>>()
            .choose(rng)
            .unwrap();
        let mut gs: GameState = GameState {
            board: Default::default(),
            player: Player::Player,
        };
        *gs.board.get_mut(loc1) = *[2, 4].choose(rng).unwrap();
        *gs.board.get_mut(loc2) = *[2, 4].choose(rng).unwrap();

        gs
    }

    pub fn take_action_mut(&mut self, action: Action) -> Result<(), IllegalActionError> {
        // TODO: test that you fail on illegal moves
        let is_correct_players_turn = match self.player {
            Player::Player => matches!(action, Action::PlayerAction(..)),
            Player::Environment => matches!(action, Action::EnvironmentAction(..)),
        };
        if !is_correct_players_turn {
            return Err(IllegalActionError(action));
        }

        match action {
            Action::PlayerAction(player_action) => {
                self.take_player_action_mut(player_action)?;
            }
            Action::EnvironmentAction(environment_action) => {
                self.take_environment_action_mut(environment_action)?;
            }
        }
        Ok(())
    }

    fn take_environment_action_mut(
        &mut self,
        action: EnvironmentAction,
    ) -> Result<(), IllegalActionError> {
        debug_assert!(matches!(self.player, Player::Environment));
        let EnvironmentAction { placement, val } = action.clone();
        let space = self.board.get_mut(placement);
        if *space != 0 {
            return Err(IllegalActionError(Action::EnvironmentAction(action)));
        }
        *space = val;
        self.player = Player::Player;
        Ok(())
    }

    fn take_player_action_mut(&mut self, action: PlayerAction) -> Result<(), IllegalActionError> {
        debug_assert!(matches!(self.player, Player::Player));
        let GameState {
            ref mut board,
            ref mut player,
        } = self;
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
        *player = Player::Environment;
        Ok(())
    }

    // TODO: Iterator of actions instead?
    pub fn get_all_actions(&self) -> Vec<Action> {
        let GameState { ref board, .. } = self;
        match self.player {
            Player::Player => {
                let mut actions: Vec<PlayerAction> = Default::default();
                for (r, c) in iproduct!((0..SIDE), (0..SIDE)) {
                    let this_item = board.get((r, c));
                    if r + 1 < SIDE
                        && (board.get((r + 1, c)) == 0 || board.get((r + 1, c)) == this_item)
                    {
                        actions.push(PlayerAction::Down);
                    } else if r >= 1
                        && (board.get((r - 1, c)) == 0 || board.get((r - 1, c)) == this_item)
                    {
                        actions.push(PlayerAction::Up);
                    } else if c + 1 < SIDE
                        && (board.get((r, c + 1)) == 0 || board.get((r, c + 1)) == this_item)
                    {
                        actions.push(PlayerAction::Right);
                    } else if c >= 1
                        && (board.get((r, c - 1)) == 0 || board.get((r, c - 1)) == this_item)
                    {
                        actions.push(PlayerAction::Left);
                    }
                }

                actions.sort();
                actions
                    .into_iter()
                    .dedup()
                    .map(|x| Action::PlayerAction(x))
                    .collect()
            }
            Player::Environment => {
                let empty_spaces = iproduct!((0..SIDE), (0..SIDE)).filter(|&x| board.get(x) == 0);
                let actions: Vec<_> = empty_spaces
                    .flat_map(|placement| {
                        [1, 2].map(|val| EnvironmentAction {
                            placement: placement.into(),
                            val,
                        })
                    })
                    .map(|env_action| Action::EnvironmentAction(env_action))
                    .collect();
                actions
            }
        }
    }

    pub fn get_random_action(&self, rng: &mut ThreadRng) -> Option<Action> {
        match self.player {
            Player::Player => {
                let mut actions = self.get_all_actions();
                if actions.len() == 0 {
                    None
                } else {
                    Some(actions.remove(rng.gen_range(0..actions.len())))
                }
            }
            Player::Environment => {
                let available_placements: Vec<_> = iproduct!((0..SIDE), (0..SIDE))
                    .filter(|&(r, c)| self.board.get((r, c)) == 0)
                    .collect();
                let random_placement = available_placements.choose(rng).map(|&x| x);
                random_placement.map(|placement| {
                    Action::EnvironmentAction(EnvironmentAction {
                        placement: placement.into(),
                        val: *[2, 4].choose(rng).unwrap(),
                    })
                })
            }
        }
    }
}

impl Display for Action {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Action::PlayerAction(pa) => match pa {
                PlayerAction::Up => writeln!(f, "Up")?,
                PlayerAction::Down => writeln!(f, "Down")?,
                PlayerAction::Left => writeln!(f, "Left")?,
                PlayerAction::Right => writeln!(f, "Right")?,
            },
            Action::EnvironmentAction(EnvironmentAction {
                placement: Placement(r, c),
                val,
            }) => writeln!(f, "({}, {}) {}", r, c, val)?,
        };
        Ok(())
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
