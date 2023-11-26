use std::error::Error;
use t2048::rules;

fn main() -> Result<(), Box<dyn Error>> {
    println!("foobar");
    rules::stroopwaffle();
    Ok(())
}
