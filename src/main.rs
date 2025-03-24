use std::env;
// A Shell prompt, utilized in Client/Server commands
use std::io::{self, Write};
use std::process::Command;
use std::path::Path;

fn print_commands() {

    println!("\nWelcome to the eIRC Shell!\nType:
            \t/list servers to list active servers you're in.
            \t/list users to list active users in your friends list.
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
            \nEnjoy.");

}


fn main() {

    print_commands();

    loop {

        print!("> ");
        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();

        // everything after the whitespace is interpreted as args to command
        let mut parts = input.trim().split_whitespace();

        // read_line leaves a trailing newline, which we'll remove with trim
        let command = parts.next().unwrap();
        let args = parts;

        match command {

            "cur" => {
                println!("Current channel");
            },

            "/list" => {
                println!("/list servers");
            },

            "cd" => {
                let new_dir = args.peekable().peek().map_or("/", |x| *x);
                let root = Path::new(new_dir);
                if let Err(e) = env::set_current_dir(&root){
                    eprintln!("{}", e);
                }
            },
            command => {
                let mut child = Command::new(command)
                    .args(args)
                    .spawn()
                    .unwrap();
            
                child.wait();
            }
        }

    }
}
