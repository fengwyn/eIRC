# tracker.py: Contains modules for server/channel management
# Tracker Object for Handling Hosts, User logs and Redirect Connections

# from common import SharedQueue    # <--- Useful if buffering is required
import logging
import threading

# <Parent Class> A tracker for managing admins and members (users or servers).
# Will be accessed asynchronically, must protect with mutex
# There are two ways to utilize the tracker, for redirect servers and for chat servers
# Redirect Servers keep track of active servers, Chat servers keep track of active users

class Tracker(threading.Thread):
    
    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str):
    
        # Initializes threading
        super().__init__()

        # Server information
        self.name = name
        self.address = address
        self.is_private = is_private
        self.passkey = passkey

        # Thread safety / Mutex
        self.lock = threading.Lock()

        # The distinction is such that we'll have 
        # inhereted child Classes Tracker Server and Chat Server
        # which'll have these values behave differently

        # NOTE: admins and members are shared resources! Utilize mutex prior to writing
        # Admins: username : address
        self.admins = dict()
        # Members: username / servername : address
        self.members = dict()

        # Add the creator as default admin
        self.add_admin(creator_user, creator_address)

    
    # Admin operations

    #Grants admin privileges to a user    
    def add_admin(self, user: str, addr: str):
    
        with self.lock:
            self.admins[user] = addr
            logging.info(f"Added admin {user}@{addr} to tracker '{self.name}'")


    #Revokes admin privileges from a user   
    def remove_admin(self, user: str):

        with self.lock:
            if user in self.admins:
                del self.admins[user]
                logging.info(f"Removed admin {user} from tracker '{self.name}'")


    #Returns a copy of current admins
    def list_admins(self) -> dict:

        with self.lock:
            admins = dict(self.admins)
            return admins


    # Member operations (users or servers)
    
    # Registers a member (user or server) to the tracker
    def add_member(self, member: str, addr: str):

        with self.lock:
            self.members[member] = addr
            logging.info(f"Added member {member}@{addr} to tracker '{self.name}'")


    # Deregisters a member from the tracker
    def remove_member(self, member: str):

        with self.lock:
            if member in self.members:
                del self.members[member]
                logging.info(f"Removed member {member} from tracker '{self.name}'")


    # Returns a copy of current members  
    def list_members(self) -> dict:

        with self.lock:
            members = dict(self.members)
            return members

    
    # Server info. setters/getters    
    def set_name(self, name: str):

        with self.lock.locked():
            self.name = name

    

    def set_address(self, address: str):

        with self.lock.locked():
            self.address = address



    def get_name(self) -> str:
        return self.name


    def get_address(self) -> str:
        return self.address

# Inhereted Class <Tracker> - Tracker Server keeps a directory of active chat servers
# When a user creates a server, it should redirect them automatically to the server 
# as well as register them as an administrator ---- This will be done on server/main.py (?)
class ServerTracker(Tracker):

    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str):
        super().__init__(name, address, creator_user, creator_address, is_private, passkey)

    
    # Adds a new chat server to the directory and grants initial administrative rights
    def register_server(self, server_name: str, server_address: str,
                        admin_user: str, admin_address: str,
                        is_private: bool, passkey: str):

        full_id = f"{server_name}"  # could be extended with address (?)
        self.add_member(full_id, server_address)
        logging.info(f"Registered chat server {server_name}@{server_address}")
        # Or we could track server-specific admin
        # Maybe use a nested Tracker per server if needed (?)

    # Returns all registered chat servers
    def get_server_list(self) -> dict:
        return self.list_members()

# Inhereted Class <Tracker> - Chat Tracker for tracking active users on a chat server
class ChatTracker(Tracker):
    
    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str):
        super().__init__(name, address, creator_user, creator_address, is_private, passkey)

    # Handles a new user joining the chat
    def user_join(self, user: str, user_address: str):  
        self.add_member(user, user_address)

    # Handles a user leaving the chat
    def user_leave(self, user: str):
        self.remove_member(user)

    # Returns all active users
    def list_active_users(self) -> dict: 
        return self.list_members()

    # Returns current chat administrators
    def list_admins(self) -> dict:
        return super().list_admins()
