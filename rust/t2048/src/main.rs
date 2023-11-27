use clap::{Parser, ValueEnum};
use std::error::Error;
use std::str::FromStr;
use t2048::rules;

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

fn main() -> Result<(), Box<dyn Error>> {
    let cli = Cli::parse();
    println!("foobar");
    rules::stroopwaffle();
    Ok(())
}
