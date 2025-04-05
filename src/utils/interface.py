# interface: Contains modules for CLI input/output and commands parsing, 
# allows users to enter shell mode or IRC mode.
# The interface shows the CLI allowing the client to enter IRC commands
# or enter CLI mode which allows ease in sending files and entering chat mode.
# Cmd Module: https://docs.python.org/3/library/cmd.html

import os
import subprocess


def print_commands():

    print("\nWelcome to the eIRC Shell!\n"
           "Type:\n"
           "\t/sh to enter shell mode and exit IRC mode.\n"
           "\t/esh to exit shell mode and enter into IRC mode.\n"
           "\t/list servers to list active servers you're in.\n"
           "\t/list users to list active users in your friends list.\n"
           "\t/current prints current channel.\n"
           "\t/whisper <user> to send direct message to user.\n"
           "\t/join <server> <key> to join private server.\n"
           "\t/accept <server> to accept server invitation.\n"
           "\t/reject <server> to reject server invitation.\n"
           "\t/leave <server> to leave server.\n"
           "\t/delete <user> to delete user from friends list.\n"
           "\t/accept <user> to accept user friend request.\n"
           "\t/reject <user> to reject user friend request.\n"
           "\t/sendfile filepath <user> to send file to user -- End user must accept sendfile request.\n"
           "\t/receivefile <user> to accept file request from user.\n"
           "\t/off to close IRC client.\n"
           "\t/commands to list all eIRC commands.\n"
           "\nEnjoy.\n")


def interface():


    while True:

        # Starts in IRC mode by default
        irc_mode = True

        command = input("$ ")

        if irc_mode is True:
            pass

        elif irc_mode is False:
            pass



def main():

    print_commands()

    interface()


main()

