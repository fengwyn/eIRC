from ..utils.packet import build_packet



# Command Handler will allow server chat rooms to handle commands externally,
# which means that server chat rooms can implement their own commands without 
# having to change the server handler, thus allowing for more modularity and 
# no longer having to reboot the server to add new commands :^)
class CommandHandler:
 
    def __init__(self, tracker, usernames):
        self.tracker = tracker
        self.usernames = usernames


    # Here, we'll route the command to the appropriate handler function
    # by simply assigning the command to its implementation
    def handle_command(self, command: str) -> bytes:

        if not command.startswith('/'):
            return None

        command = command.strip()
        
        # Map commands to their handler functions
        # Doing it this way functions similar to a switch statement
        command_handlers = {
            '/users': self.handle_users,
            '/leave': self.handle_leave,
            '/current': self.handle_current,
            '/whisper': self.handle_whisper
        }

        # Get the base command without arguments
        base_command = command.split()[0]
        handler = command_handlers.get(base_command)
        
        if handler:
            # Only pass command to whisper handler since it needs the arguments
            if base_command == '/whisper':
                return handler(command)
            return handler()
        
        return None


    # Handle /users command
    def handle_users(self) -> bytes:
    
        user_list = ", ".join(self.usernames)
        return build_packet("Users", user_list)


    # Handle /leave command
    def handle_leave(self) -> bytes:

        return build_packet("LEAVE", "Leaving chat room...")


    # Handle /current command
    def handle_current(self) -> bytes:

        curr_srv_name = self.tracker.get_name()
        return build_packet("Currently in:", curr_srv_name)


    # Handle /whisper command
    # NOTE: This command is also handled in server.py
    # we're just building the packet here
    def handle_whisper(self, command: str) -> bytes:

        parts = command.split(maxsplit=2)  # Split into ['/whisper', 'username', 'message']
        
        if len(parts) < 3:
            return build_packet("ERROR", "Usage: /whisper <username> <message>")
        
        whisper_user = parts[1]
        message = parts[2]
        
        if whisper_user not in self.usernames:
            return build_packet("ERROR", f"User '{whisper_user}' not found")
        
        return build_packet("WHISPER", f"{whisper_user}|{message}")
