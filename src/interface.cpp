// interface: Contains modules for CLI input/output and commands parsing, allows users to enter shell mode or IRC mode.
// The interface shows the CLI allowing the client to enter IRC commands
// or enter CLI mode which allows ease in sending files and entering chat mode.
#include "interface.h"


void print_commands() {

    printf("\nWelcome to the eIRC Shell!\n"
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
           "\nEnjoy.\n");

}


// Helper function: Trim leading and trailing whitespace.
char *trim_whitespace(char *str) {
    char *end;
    while(*str == ' ' || *str == '\t') str++;
    if(*str == 0)  // All spaces?
        return str;
    end = str + strlen(str) - 1;
    while(end > str && (*end == ' ' || *end == '\t')) end--;
    *(end+1) = 0;
    return str;
}

void execute_cd(char *input) {
    // Skip the "cd" part.
    char *arg = input + 2;  // after "cd"
    arg = trim_whitespace(arg);
    
    // If argument is wrapped in quotes, remove them.
    size_t len = strlen(arg);
    if(len > 1 && ((arg[0] == '"' && arg[len-1] == '"') || (arg[0] == '\'' && arg[len-1] == '\''))) {
        arg[len-1] = '\0';  // remove trailing quote
        arg++;              // move past the leading quote
    }
    
    // If no argument, default to "/".
    if(strlen(arg) == 0) {
        arg = "/";
    }
    
    if(chdir(arg) != 0) {
        perror("chdir error");
    }
}


int interface() {

    int in_shell_mode = 0;
    char input[1024];
    char cwd[PATH_MAX];

    while (1) {
        // Display prompt depending on mode.
        if (in_shell_mode) {
    
            if (getcwd(cwd, sizeof(cwd)) != NULL) {
                printf("[%s]$ ", cwd);
    
            } else {
    
                printf("> ");
    
            }
    
        } else {
    
            printf("> ");
    
        }
    
        fflush(stdout);

        // Read input from user
        if (!fgets(input, sizeof(input), stdin)) {
            break; // Exit on error or EOF
        }

        // Remove newline
        input[strcspn(input, "\n")] = '\0';

        // Mode switch commands
        if (strcmp(input, "/sh") == 0) {

            in_shell_mode = 1;
            printf("Entered shell mode. Type '/esh' to exit.\n");
            continue;

        } else if (strcmp(input, "/esh") == 0) {

            in_shell_mode = 0;
            printf("Exited shell mode. Returning to IRC mode.\n");
            continue;

        }

        if (in_shell_mode) {
            // In shell mode, process commands
            // Tokenize the input string
            char *command = strtok(input, " ");
            if (command == NULL) continue;

            if (strcmp(command, "cd") == 0) {

                // Handle "cd" command
                char *new_dir = strtok(NULL, " ");
                if (new_dir == NULL) {
                    new_dir = "/";
                }

                if (chdir(new_dir) != 0) {
                    perror("chdir error");

                }

            } else {

                // For other commands, execute using system()
                int ret = system(input);
                if (ret == -1) {
                    perror("Command error");
                }

            }

        } else {

            // In IRC mode, simulate command handling
            if (strcmp(input, "/list") == 0) {
                printf("/list servers\n");

            } else if (strcmp(input, "/current") == 0) {
                printf("Current channel\n");

            } else if (strcmp(input, "/commands") == 0) {
                print_commands();

            } else {
                printf("IRC Command: %s\n", input);
            }

        }
    }

    return 0;
}
