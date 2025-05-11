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
    
    commands = {"/sh", "/esh", "/servers", "/users", "/current", "/whisper", 
            "/join", "/accept", "/reject", "/leave", "/delete", 
            "/reject", "/sendfile", "/receivefile", 
            "/off", "/commands"}

    return commands

# Global Text Section
def get_command_text() -> str:
    
    command_text = '''/sh: to enter shell mode and exit IRC mode.
        /esh: to exit shell mode and enter into IRC mode.
        /servers: to list active servers you're in.
        /users: to list active users in your friends list.
        /current: prints current channel.
        /whisper <user>: to send direct message to user.
        /join <server> <key>: to join private server.
        /accept <server>: to accept server invitation.
        /reject <server>: to reject server invitation.
        /leave <server>: to leave server.
        /delete <user>: to delete user from friends list.
        /accept <user>: to accept user friend request.
        /reject <user>: to reject user friend request.
        /sendfile filepath <user>: to send file to user -- End user must accept sendfile request.
        /receivefile <user>: to accept file request from user.
        /off: to close IRC client.
        /commands: to list all eIRC commands.'''

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
                    # current_path_split = str(current_path).split('/')
                    # cur_path_size = len(current_path_split)
                    # cur_path = current_path_split[:]
                    # print(f"Path splits: {current_path_split} ")

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
    