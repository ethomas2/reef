use std::error::Error;

use clap::{Parser, ValueEnum};

#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum PlayerType {
    Random,
    Human,
}

#[derive(Debug, Parser)]
struct Cli {
    player1: PlayerType,
    player2: PlayerType,
}

enum Player {
    Player1,
    Player2,
}

#[derive(Copy, Clone)]
enum Space {
    Player1,
    Player2,
    Empty,
}

struct Board([[Space; 7]; 6]);
struct GameState {
    board: Board,
    player: Player,
}

impl GameState {
    fn new() -> Self {
        Self {
            board: Board([[Space::Empty; 7]; 6]),
            player: Player::Player1,
        }
    }

    fn to_console(&self) -> String {
        todo!();
    }
}

#[derive(Debug)]
struct Action(u8, u8);

fn get_action(player_type: PlayerType, gamestate: &GameState) -> Option<Action> {
    todo!();
}

fn take_action_mut(gamestate: &mut GameState, action: Action) {
    todo!();
}

fn main() -> Result<(), Box<dyn Error>> {

    let cli = Cli::parse();
    let mut gamestate = GameState::new();


    loop {
        let player_type = match gamestate.player {
            Player::Player1 => cli.player1,
            Player::Player2 => cli.player2,
        };

        let Some(action) = get_action(player_type, &gamestate) else {
            println!("Returned None for action. Breaking");
            break;
        };
        println!("{:?}", action);
        take_action_mut(&mut gamestate, action);
        println!("{}", gamestate.to_console())
    }


    println!("Hello, world!");
    Ok(())
}
