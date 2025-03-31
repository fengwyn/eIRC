// main.rs: Project entry point, allows launching client or server based on Command Line Arguments.
mod interface;
use interface::*;

mod client;
use client::*;

mod server;
use server::*;

// Command Line Arguments
use std::env;

fn main() {

    let args: Vec<String> = env::args().collect();
    let connection_mode = &args[1];

    println!("Connection mode: {connection_mode}\n");

    print_commands();
    
    match connection_mode {

        "1" => {
            client();
        }

        "2" => {
            server();
        }
        
        _ => {
            println!("Bad Choice");
        }
    }


    interface();



}
