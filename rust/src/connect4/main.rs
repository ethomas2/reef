use std::convert::TryFrom;
use std::io;
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

#[derive(Debug, Copy, Clone)]
struct Action(u8, u8);

impl TryFrom<&str> for Action {
    type Error = &'static str;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        let mut parts = value.split(" ");
        let row: u8 = parts.next().ok_or("Not enough parts")?.parse().map_err(|_| "not an int")?;
        let col: u8 = parts.next().ok_or("Not enough parts")?.parse().map_err(|_| "not an int")?;
        if let Some(_) = parts.next() {
            return Err("too many parts");
        }
        Ok(Action(row, col))
    }

}

fn get_human_action(_: &GameState) -> Option<Action> {
    loop  {
        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let maybe_action: Result<Action, _> =  input.as_str().try_into();
        match  maybe_action {
            Ok(action) => {return Some(action);},
            Err(err) => {println!("Not valid {}", err)}
        }
    }
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

        let Some(action) = (match player_type {
            PlayerType::Human => get_human_action(&gamestate),
            PlayerType::Random => todo!(),
        }) else {
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
