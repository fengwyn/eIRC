# main: Project entry point, allows launching client or server based on Command Line Arguments.

# TODO: Encapsulate within classes, utilize the interface for swapping between IRC and Shell mode


import os
import sys
import subprocess
import shlex
from pathlib import Path



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



def interface():


    in_shell_mode = False

    while True:

        if in_shell_mode:

            try:
                current_path = Path(os.getcwd())
                print(f"[{current_path}]$ ", end="")

            except Exception as e:
                print(f"Error getting current directory: {e}")
                print("> ", end="")
        else:

            print("> ", end="")

        # Get user input
        input_command = input().strip()

        if input_command == "/sh":

            in_shell_mode = True
            print("Entered shell mode. Type 'esh' to exit.")
            continue

        elif input_command == "/esh":

            in_shell_mode = False
            print("Exited shell mode. Returning to IRC mode.")
            continue

        if in_shell_mode:

            try:
                # Use shlex.split to parse quoted strings
                parts = shlex.split(input_command)

            except ValueError as e:

                print(f"Error parsing command: {e}")
                continue

            if not parts:
                continue

            command = parts[0]
            args = parts[1:]

            if command == "cd":

                new_dir = ' '.join(args) if args else "."

                try:
                    os.chdir(new_dir)

                except FileNotFoundError as e:
                    print(f"Error changing directory: {e}")

                except PermissionError as e:
                    print(f"Permission error: {e}")

            else:

                try:
                    subprocess.run([command] + args)
                except FileNotFoundError as e:
                    print(f"Command error: {e}")

        else:

            if input_command == "/list":
                print("/list servers")

            elif input_command == "/current":
                print("Current channel")

            elif input_command == "/commands":
                print_commands()

            else:
                print(f"IRC Command: {input_command}")



if __name__ == "__main__":
    interface()
