# interface: Contains modules for CLI input/output and commands parsing, 
# allows users to enter shell mode or IRC mode.
# The interface shows the CLI allowing the client to enter IRC commands
# or enter CLI mode which allows ease in sending files and entering chat mode.
# Cmd Module: https://docs.python.org/3/library/cmd.html


import os
import sys
import subprocess
import shlex
from pathlib import Path


# Implemented IRC Commands (useful if desired parsing by array)
def get_commands():
    
    commands = {"/sh", "/irc", "/servers", "/users", "/current", "/whisper", 
            "/join", "/accept", "/reject", "/leave", "/delete", 
            "/reject", "/sendfile", "/receivefile", "/exit",
            "/off", "/commands"}

    return commands

# Global Text Section
def get_command_text() -> str:
    
    command_text = '''\t--- eIRC Commands ---

        /sh: Enter shell mode and exit IRC mode.
        /irc: Exit shell mode and enter into IRC mode.
        /commands: List all eIRC commands.

        /servers: List active servers you're in.
        /join <server> <key>: Join private server.
        /accept <server>: Accept server invitation.
        /reject <server>: Reject server invitation.
        
        /accept <user>: Accept user friend request.
        /reject <user>: Reject user friend request.
        /delete <user>: Delete user from friends list.

        /exit: Exit IRC Tracker Server.
        /off: Close IRC client.

        \t--- Chat Room Commands ---

        /current: Print current channel.
        /users: List active users in your friends list.
        /leave <server>: Leave server.

        /whisper <user>: Send direct message to user.
        /sendfile filepath <user>: Send file to user -- End user must accept sendfile request.
        /receivefile <user>: Accept file request from user.

'''

    return command_text

# Prints available IRC Commands
def print_commands():

    print(get_command_text())

# Interface, can swap between IRC and Shell mode
def interface():

    print_commands()

    # Starts in IRC mode
    in_shell_mode = False

    while True:

        # Giant Try block, for handling Keyboard Interrupts :)
        try:

            # If shell mode display Shell-like interface    ---- Will be skipped during first iter
            if in_shell_mode:

                try:
                    current_path = Path(os.getcwd())
                    print(f"[{current_path}]$ ", end="")

                except Exception as e:
                    print(f"Error getting current directory: {e}")
                    print("> ", end="")
                    # Add logging exception in pass :)
                    pass
            
            else:   # eoif
                print("> ", end="")


            ## Get user input   ##
            input_command = input().strip()
            ##                  ##

            # If user types /sh ---- Enter Shell mode
            if input_command == "/sh":

                in_shell_mode = True
                print("Entered shell mode. Type '/irc' to exit shell mode.")
                continue

            # If user types /irc ---- Enter IRC mode
            elif input_command == "/irc":

                in_shell_mode = False
                print("Exited shell mode. Returning to IRC mode.")
                continue
            # eoif

            # Parse shell commands
            if in_shell_mode:

                try:
                    # Use shlex.split to parse quoted strings
                    # This is utilized to handle cases such as: $ cd 'Directory with Spaces'
                    parts = shlex.split(input_command)

                except ValueError as e:

                    print(f"Error parsing command: {e}")
                    # Log errors here :)
                    continue

                if not parts:
                    continue

                command = parts[0]
                args = parts[1:]

                # Change Directory requires its own case management as noted above with <parts>
                if command == "cd":

                    # If provided a destination to cd go to it, else stay in cur dir.
                    new_dir = ' '.join(args) if args else "."

                    # Useful exception for handling erroneous entries.
                    try:
                        os.chdir(new_dir)

                    except FileNotFoundError as e:
                        print(f"Error changing directory: {e}")

                    except PermissionError as e:
                        print(f"Permission error: {e}")

                # eoif  ---- Non-$ cd cases
                else:
                    # We'll trust the OS to manage the command(s) :)
                    try:
                        subprocess.run([command] + args)
                    except FileNotFoundError as e:
                        print(f"Command error: {e}")
            
            # Handle IRC commands
            # NOTE: This'll probably be obsolete given that client/client.py handles this now
            else:
                # Use match-case (switch) for mass conditional handling
                match input_command:

                    case "/commands":
                        print_commands()

                    case "/servers":
                        print("Listing active servers...")

                    case "/current":
                        print("Current channel: ")

                    case _:
                        print("Invalid Command!")


        # Manage any on-going critical processes, i.e sockets for safe shutdown
        except KeyboardInterrupt:
            print("\tKeyboard Interrupt...\n\tSafely shutting down application.")
            sys.exit()
            pass



if __name__ == "__main__":

    interface()
    