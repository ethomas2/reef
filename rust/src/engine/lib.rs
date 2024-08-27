use rand::rngs;
use rand::Rng;
use std::io;

/// The state needed for a game. I.e. for 2048 the board
pub trait GameState {
    type TakeActionError;
    type Action;
    type AllActionsIter: Iterator<Item = Self::Action> + ExactSizeIterator;

    fn get_all_actions(&self) -> Self::AllActionsIter;

    fn take_action_mut(&mut self, action: Self::Action) -> Result<(), Self::TakeActionError>;
}

/// A thing that takes in a game and returns the action to take for a given game state
pub trait Engine<G: GameState> {
    fn get_action(&mut self, game: G) -> Option<G::Action>;
}

pub trait ToConsole: GameState {
    fn to_console() -> String;
}

pub struct RandomEngine {
    rng: rngs::ThreadRng,
}

impl<G: GameState> Engine<G> for RandomEngine {
    fn get_action(&mut self, gamestate: G) -> Option<G::Action> {
        let mut actions = gamestate.get_all_actions();
        let idx = self.rng.gen_range(0..actions.len());
        let result = actions.nth(idx);
       result
    }
}

pub struct HumanEngine<G: GameState> {
    str_to_action: Box<dyn Fn(&str) -> Option<G::Action>>

}

impl<G: GameState> Engine<G> for HumanEngine<G> {
    fn get_action(&mut self, _gamestate: G) -> Option<G::Action>
    {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let action = (self.str_to_action)(&input);
        action
    }
}
