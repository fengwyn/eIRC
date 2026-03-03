# !!! CLASS/FUNCTIONAL DEFINITIONS

# tracker.py: Contains modules for server/channel management
# Tracker Object for Handling Hosts, User logs and Redirect Connections
#
# Dual-mode: If a redis.Redis client is passed, admins/members are stored
# in Redis hashes (persistent, atomic).  Otherwise falls back to in-memory
# dicts protected by threading.Lock (original behaviour).

import logging
import threading


# <Parent Class> A tracker for managing admins and members (users or servers).
# Will be accessed asynchronically, must protect with mutex (dict mode)
# or rely on Redis atomicity (Redis mode).
# There are two ways to utilize the tracker, for redirect servers and for node servers
# Redirect Servers keep track of active servers, node servers keep track of active users

class Tracker(threading.Thread):

    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str,
                 redis_client=None):

        # Initializes threading
        super().__init__()

        # Server information
        self.name = name
        self.address = address
        self.is_private = is_private
        self.passkey = passkey

        # Redis client (None = dict fallback)
        self.redis = redis_client
        self.key_prefix = f"eirc:{name}"

        # Thread safety / Mutex (used in dict mode)
        self.lock = threading.Lock()

        # In-memory fallback (only used when self.redis is None)
        if self.redis is None:
            self.admins = dict()
            self.members = dict()

        # Add the creator as default admin
        self.add_admin(creator_user, creator_address)


    # Admin operations

    #Grants admin privileges to a user
    def add_admin(self, user: str, addr: str):

        if self.redis:
            self.redis.hset(f"{self.key_prefix}:admins", user, addr)
        else:
            with self.lock:
                self.admins[user] = addr

        logging.info(f"Added admin {user}@{addr} to tracker '{self.name}'")


    #Revokes admin privileges from a user
    def remove_admin(self, user: str):

        if self.redis:
            self.redis.hdel(f"{self.key_prefix}:admins", user)
        else:
            with self.lock:
                if user in self.admins:
                    del self.admins[user]

        logging.info(f"Removed admin {user} from tracker '{self.name}'")


    #Returns a copy of current admins
    def list_admins(self) -> dict:

        if self.redis:
            return self.redis.hgetall(f"{self.key_prefix}:admins")

        with self.lock:
            return dict(self.admins)


    # Member operations (users or servers)

    # Registers a member (user or server) to the tracker
    def add_member(self, member: str, addr: str):

        if self.redis:
            self.redis.hset(f"{self.key_prefix}:members", member, addr)
        else:
            with self.lock:
                self.members[member] = addr

        logging.info(f"Added member {member}@{addr} to tracker '{self.name}'")


    # Deregisters a member from the tracker
    def remove_member(self, member: str):

        if self.redis:
            self.redis.hdel(f"{self.key_prefix}:members", member)
        else:
            with self.lock:
                if member in self.members:
                    del self.members[member]

        logging.info(f"Removed member {member} from tracker '{self.name}'")


    # Returns a copy of current members
    def list_members(self) -> dict:

        if self.redis:
            return self.redis.hgetall(f"{self.key_prefix}:members")

        with self.lock:
            return dict(self.members)


    # Server info. setters/getters
    def set_name(self, name: str):

        with self.lock:
            old_prefix = self.key_prefix
            self.name = name
            self.key_prefix = f"eirc:{name}"

            # If Redis, migrate keys to new prefix
            if self.redis and old_prefix != self.key_prefix:
                for suffix in (":admins", ":members"):
                    data = self.redis.hgetall(old_prefix + suffix)
                    if data:
                        self.redis.hset(self.key_prefix + suffix, mapping=data)
                    self.redis.delete(old_prefix + suffix)


    def set_address(self, address: str):

        with self.lock:
            self.address = address


    def get_name(self) -> str:
        return self.name


    def get_address(self) -> str:
        return self.address



# Inhereted Class <Tracker> - Tracker Server keeps a directory of active node servers
# When a user creates a server, it should redirect them automatically to the server
# as well as register them as an administrator ---- This will be done on server/main.py (?)
class ServerTracker(Tracker):

    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str,
                 redis_client=None):

        super().__init__(name, address, creator_user, creator_address,
                         is_private, passkey, redis_client=redis_client)
        # In-memory fallback for server metadata
        if self.redis is None:
            self.server_metadata = {}


    # Adds a new node server to the directory and grants initial administrative rights

    # NOTE: server_address will contain 'IP:PORT'
    def register_server(self, server_name: str, server_address: str,
                        admin_user: str, admin_address: str,
                        is_private: bool, passkey: str):

        self.add_member(server_name, server_address)

        # Store server metadata
        meta = {
            'is_private': str(is_private),
            'passkey': passkey,
            'admin_user': admin_user,
            'admin_address': admin_address
        }

        if self.redis:
            self.redis.hset(f"{self.key_prefix}:meta:{server_name}", mapping=meta)
        else:
            # Dict mode stores native Python types
            meta['is_private'] = is_private
            self.server_metadata[server_name] = meta

        logging.info(f"Registered node server {server_name}@{server_address}")


    # Returns all registered node servers
    def get_server_list(self) -> dict:
        return self.list_members()


    # Returns server metadata including privacy settings
    def get_server_info(self, server_name: str) -> dict:

        if self.redis:
            data = self.redis.hgetall(f"{self.key_prefix}:meta:{server_name}")
            if not data:
                return None
            # Cast is_private string back to bool
            data['is_private'] = data.get('is_private', 'False') == 'True'
            return data

        with self.lock:
            return self.server_metadata.get(server_name)



# Inhereted Class <Tracker> - Node Tracker for tracking active users on a node server
class NodeTracker(Tracker):

    def __init__(self, name: str, address: str,
                 creator_user: str, creator_address: str,
                 is_private: bool, passkey: str,
                 redis_client=None):

        super().__init__(name, address, creator_user, creator_address,
                         is_private, passkey, redis_client=redis_client)

    # Handles a new user joining the node
    def user_join(self, user: str, user_address: str):
        self.add_member(user, user_address)

    # Handles a user leaving the node
    def user_leave(self, user: str):
        self.remove_member(user)

    # Returns all active users
    def get_active_users_list(self) -> dict:
        return self.list_members()

    # Returns current node administrators
    def get_admin_list(self) -> dict:
        return super().list_admins()