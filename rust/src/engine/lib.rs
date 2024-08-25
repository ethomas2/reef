use rand::rngs;
use rand::Rng;
use std::io;

/// The state needed for a game. I.e. for 2048 the board
pub trait GameState {
    type Error;
    type Action;

    fn get_all_actions(&self) -> Vec<Self::Action>;

    fn take_action_mut(&mut self, action: Self::Action) -> Result<(), Self::Error>;
}

/// A thing that takes in a game and returns the action to take for a given game state
pub trait Engine {
    fn get_action<G: GameState + ToConsole>(&mut self, game: G) -> G::Action;
}

pub trait ToConsole: GameState {
    fn to_console() -> String;
}

pub struct RandomEngine {
    rng: rngs::ThreadRng,
}

impl Engine for RandomEngine {
    fn get_action<G: GameState>(&mut self, gamestate: G) -> G::Action {
        let mut actions = gamestate.get_all_actions();
        actions.remove(self.rng.gen_range(0..actions.len()))
    }
}

pub struct HumanEngine {}

impl Engine for HumanEngine {
    fn get_action<G: GameState + ToConsole>(&mut self, _gamestate: G) -> G::Action {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        todo!()
    }
}
