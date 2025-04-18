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


# IRC Commands
def print_commands():

    print("\nWelcome to the eIRC Shell!")
    print("Type:")
    print("\t/sh to enter shell mode and exit IRC mode.")
    print("\t/esh to exit shell mode and enter into IRC mode.")
    print("\t/list servers to list active servers you're in.")
    print("\t/list users to list active users in your friends list.")
    print("\t/current prints current channel.")
    print("\t/whisper <user> to send direct message to user.")
    print("\t/join <server> <key> to join private server.")
    print("\t/accept <server> to accept server invitation.")
    print("\t/reject <server> to reject server invitation.")
    print("\t/leave <server> to leave server.")
    print("\t/delete <user> to delete user from friends list.")
    print("\t/accept <user> to accept user friend request.")
    print("\t/reject <user> to reject user friend request.")
    print("\t/sendfile filepath <user> to send file to user -- End user must accept sendfile request.")
    print("\t/receivefile <user> to accept file request from user.")
    print("\t/off to close IRC client.")
    print("\t/commands to list all eIRC commands.")
    print("\nEnjoy.")


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

                if input_command == "/list":
                    print("/list servers")

                elif input_command == "/current":
                    print("Current channel")

                elif input_command == "/commands" or input_command == "/help":
                    print_commands()

                else:
                    print(f"IRC Command: {input_command}")


        # Manage any on-going critical processes, i.e sockets for safe shutdown
        except KeyboardInterrupt:

            print("\tKeyboard Interrupt...\n\tSafely shutting down application.")
            sys.exit()
            pass



if __name__ == "__main__":

    interface()
