// interface.rs: Contains modules for CLI input/output and commands parsing, allows users to enter shell mode or IRC mode.
// The interface shows the CLI allowing the client to enter IRC commands
// or enter CLI mode which allows ease in sending files and entering chat mode.

use std::env;
use std::io::{self, Write};
use std::process::Command;
use std::path::Path;

pub fn print_commands() {

    println!("\nWelcome to the eIRC Shell!\nType:
            \t/sh to enter shell mode and exit IRC mode.
            \t/esh to exit shell mode and enter into IRC mode.
            \t/list servers to list active servers you're in.
            \t/list users to list active users in your friends list.
            \t/current prints current channel.
            \t/whisper <user> to send direct message to user.
            \t/join <server> <key> to join private server.
            \t/accept <server> to accept server invitation.
            \t/reject <server> to reject server invitation.
            \t/leave <server> to leave server.
            \t/delete <user> to delete user from friends list.
            \t/accept <user> to accept user friend request.
            \t/reject <user> to reject user friend request.
            \t/sendfile filepath <user> to send file to user -- End user must accept sendfile request.
            \t/receivefile <user> to accept file request from user.
            \t/off to close IRC client.
            \t/commands to list all eIRC commands.
            \nEnjoy.");

}


pub fn interface() {


    let mut in_shell_mode: bool = false;

    loop {

        if in_shell_mode {
            match env::current_dir() {
                Ok(path) => print!("[{}]$ ", path.display()),
                Err(_) => print!("> "),
            }
        } else {
            
            print!("> ");
        }

        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let input = input.trim();

        if input == "/sh" {

            in_shell_mode = true;
            println!("Entered shell mode. Type 'esh' to exit.");
            continue;

        } else if input == "/esh" {

            in_shell_mode = false;
            println!("Exited shell mode. Returning to IRC mode.");
            continue;

        }

        if in_shell_mode {

            let mut parts = input.split_whitespace();
            let command = parts.next().unwrap_or("");
            let args = parts;

            match command {

                "cd" => {

                    let new_dir = args.peekable().peek().map_or("/", |x| *x);
                    let root = Path::new(new_dir);
                    if let Err(e) = env::set_current_dir(&root) {
                        eprintln!("{}", e);
                    }

                },
                command => {

                    match Command::new(command).args(args).spawn() {
                        Ok(mut child) => {
                            child.wait().unwrap();
                        },
                        Err(e) => eprintln!("Command error: {}", e),
                    }
                }

            }

        } else {

            match input {

                "/list" => println!("/list servers"),
                "/current" => println!("Current channel"),
                "/commands" => print_commands(),
                _ => println!("IRC Command: {}", input),
            }

        }
    }
}
