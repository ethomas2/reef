mod rules;

// use self::rules;
extern crate engine;
use clap::{Parser, ValueEnum};
use engine::foo;
use rand;
use rand::Rng;
use std::error::Error;
use std::io;

#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum)]
enum PlayerType {
    Random,
    Mcts,
    Human,
    Minimax,
}

#[derive(Debug, Parser)]
struct Cli {
    #[arg(short, long, value_enum)]
    player_type: PlayerType,
}

fn human_play_1player_game(gamestate: &mut rules::GameState) {
    let mut rng = rand::thread_rng();
    // display
    println!("{}", gamestate.to_console().unwrap());
    loop {
        // get action from human
        let action: rules::Action;
        loop {
            let mut input = String::new();
            io::stdin().read_line(&mut input).unwrap(); // TODO: lock()?
            let action_result = input.parse();
            match action_result {
                Ok(a) => {
                    action = rules::Action::PlayerAction(a);
                    break;
                }
                Err(_) => {
                    println!("Could not parse action");
                }
            }
        }

        // take action and display
        gamestate
            .take_action_mut(action)
            .expect("Player took an illegal action");
        println!("{}", gamestate.to_console().unwrap());

        // get action from engine
        let random_environment_action = {
            let mut actions = gamestate.get_all_actions();
            if actions.len() == 0 {
                None
            } else {
                let idx = rng.gen_range(0..actions.len());
                Some(actions.remove(idx))
            }
        };
        match random_environment_action {
            None => {
                println!("No more actions available. Breaking");
                break;
            }
            Some(action) => {
                println!("Enviornment Action: {}", action);
                gamestate
                    .take_action_mut(action)
                    .expect("Environment took an illegal action");
                println!("{}", gamestate.to_console().unwrap());
            }
        }
    }
}

fn random_game(gamestate: &mut rules::GameState) {
    let mut rng = rand::thread_rng();
    // display
    println!("{}", gamestate.to_console().unwrap());
    loop {
        // get random action
        let action = {
            let mut random_actions = gamestate.get_all_actions();
            let rand_idx = rng.gen_range(0..random_actions.len());
            random_actions.remove(rand_idx)
        };
        println!("Random Player Action :: {}", action);

        // take action and display
        gamestate
            .take_action_mut(action)
            .expect("Player took an illegal action");
        println!("{}", gamestate.to_console().unwrap());

        // get action from engine
        let random_environment_action = {
            let mut actions = gamestate.get_all_actions();
            if actions.len() == 0 {
                None
            } else {
                let idx = rng.gen_range(0..actions.len());
                Some(actions.remove(idx))
            }
        };
        match random_environment_action {
            None => {
                println!("No more actions available. Breaking");
                break;
            }
            Some(action) => {
                println!("Enviornment Action: {}", action);
                gamestate
                    .take_action_mut(action)
                    .expect("Environment took an illegal action");
                println!("{}", gamestate.to_console().unwrap());
            }
        }
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let cli = Cli::parse();
    let mut rng = rand::thread_rng();
    let mut gamestate = rules::GameState::init_game(&mut rng);
    match cli.player_type {
        PlayerType::Human => human_play_1player_game(&mut gamestate),
        PlayerType::Random => random_game(&mut gamestate),
        PlayerType::Mcts => unimplemented!(),
        PlayerType::Minimax => unimplemented!(),
    }
    Ok(())
}
