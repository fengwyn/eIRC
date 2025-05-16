import socket
import threading
import argparse
from ..utils.tracker import ServerTracker
from ..utils.packet import unpack_packet, build_packet
from ..utils.interface import get_command_text
# The implemented Server object shall be utilized as a Chat Room for the redirect server
from .server import Server as ChatRoomServer

# Port allocation helper (increments port number)
class PortAllocator:

    def __init__(self, start_port=9000):
        self.lock = threading.Lock()
        self.next_port = start_port

    
    def allocate(self):

        with self.lock:
            port = self.next_port
            self.next_port += 1
            return port

# Main tracker daemon 
# (Do note, ServerTracker is already defined, 
# this object instantiates it whilst implementing the redirect functionalities)
class TrackerDaemon:

    def __init__(self, host, port, allocator, MAXIMUM_CONNECTIONS, MESSAGE_LENGTH):

        self.host = host
        self.port = port
        self.allocator = allocator
        self.max_conns = MAXIMUM_CONNECTIONS
        self.msg_length = MESSAGE_LENGTH

        # Pre-calculate tracker address for registration
        address = f"{host}:{port}"
        # Instantiate ServerTracker positionally to match its __init__ signature
        self.tracker = ServerTracker(
            "GlobalTracker",
            address,
            "tracker",
            address,
            False,
            ""
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(self.max_conns)

        print(f"Tracker listening on {host}:{port}")


    def start(self):

        try:
            while True:
                conn, addr = self.sock.accept()
                # Running as a daemon allows us to encapsulate the object and therefore, 
                # allow the Client/Server model to deploy Chat Servers in a Factory design pattern
                threading.Thread(target=self.handle, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("Shutting down tracker.")
            self.sock.close()
        except Exception as e:
            print(f"TrackerDaemon Exception: {e}")
            self.sock.close()
    
    def handle(self, conn, addr):

        # conn.send(b"Welcome to eIRC - Tracker Server!")
        packet = None
        packet = build_packet("Welcome to eIRC\nTracker Server", get_command_text())
        conn.send(packet)
        
        try:
            while True:
                
                packet = conn.recv(self.msg_length)

                if not packet:
                    break

                # Unpack packet
                read_packet: dict() = unpack_packet(packet)
                header, body, date = read_packet['header'], read_packet['body'], read_packet['date']
                # Initialize command buffer
                command = None

                if not body.startswith('/'):
                    print("eIRC - Command Usage")
                    packet = build_packet("Command Usage", get_command_text())
                    conn.send(packet)
                    continue

                if body.startswith('/'):

                    # We'll tokenize the command
                    tokens = body.strip().split()
                    # command = <command> , args = [<args 1>, ..., <args n>]
                    command, *args = tokens

                    print(f"Command: {command}\tArguments: {args}")

                    # Utilize switch-case for handling all commands, or integrate via proper function/module
                    
                    match command:

                        # Create a chat room
                        case "/create":

                            if len(args) < 3:
                                packet = build_packet('''Incorrect Usage: Servername in <name>,              
                    Your (or default) username for administrator's username in <admin_user>,
                    If the server will be private input 1, else 0 in <private>,
                    If private input passkey in <passkey>''', 

                    "\n/create <name> <admin_user> <private> <passkey>")

                                conn.send(packet)
                                continue
                            
                            name = args[0]
                            
                            # Check if a server name is already in use
                            existing_servers = self.tracker.get_server_list()
                            if name in existing_servers:
                                packet = build_packet("ERROR", f"Server name '{name}' is already taken. Choose a different name.")
                                conn.send(packet)
                                continue

                            admin_user = args[1]
                            isPrivate = args[2]
                            passkey = ""

                            if isPrivate == "1" or isPrivate == "true":
                                isPrivate = True
                                passkey = args[3]
                            else:
                                isPrivate = False

                            # allocate a port for new chat server
                            chat_port = self.allocator.allocate()

                            # start chat server instance
                            # register in tracker
                            admin_address = f"{addr[0]}:{addr[1]}"
                            chat_srv = ChatRoomServer(self.host, chat_port, self.max_conns, self.msg_length, 
                                                    name, admin_user, admin_address, isPrivate, passkey)
                            
                            threading.Thread(target=chat_srv.server_start, daemon=True).start()

                            self.tracker.register_server(
                                name,
                                f"{self.host}:{chat_port}",
                                admin_user=admin_user,
                                admin_address=admin_address,
                                is_private=isPrivate,
                                passkey=passkey
                            )

                            packet = build_packet("CHAT CREATED", f"{name} {self.host} {chat_port}")
                            conn.send(packet)

                        # List active servers
                        case "/servers":

                            servers = self.tracker.get_server_list()
                            resp = "ACTIVE_SERVERS\n"
                            for sname, saddr in servers.items():
                                resp += f"{sname} @ {saddr}\n"

                            packet = build_packet("/servers", resp)
                            conn.send(packet)

                        # Join a chat room
                        case "/join":

                            if len(args) < 1:
                                packet = build_packet("ERROR Usage", "/join <name> [passkey]")
                                conn.send(packet)
                                continue
                        
                            name = args[0]
                            servers = self.tracker.get_server_list()    # <- This is a dict()
                            
                            if name in servers:
                                # Get server info from tracker to check if it's private
                                server_info = self.tracker.get_server_info(name)
                                
                                if server_info['is_private']:
                                    # Check if passkey was provided
                                    if len(args) < 2:
                                        packet = build_packet("ERROR", f"Server '{name}' is private. Please provide a passkey: /join {name} <passkey>")
                                        conn.send(packet)
                                        continue
                                    
                                    # Verify passkey
                                    if args[1] != server_info['passkey']:
                                        packet = build_packet("ERROR", "Incorrect passkey")
                                        conn.send(packet)
                                        continue

                                packet = build_packet("JOIN", f"{servers[name]}")
                                print(f"JOIN: {servers[name]} @ {servers[name]}")
                                conn.send(packet)

                            else:
                                packet = build_packet("ERROR", "Server not found")
                                conn.send(packet)

                        # Exit tracker
                        case "/exit":

                            packet = build_packet("EXIT", "Closing connection...")
                            conn.send(packet)
                            try:
                                conn.close()
                                break
                            except Exception as e:
                                print(f"\nFailed to close connection: {e}")


                        # Handle everything else
                        case _:
                            packet = build_packet("ERROR", "Unknown command")
                            conn.send(packet)


                        # eof case
                    # eof switch
                # eof '/'
                pass
            # eof while True
        # eof try
        finally:
            conn.close()
    # eo def
# eof class


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Tracker Server for chat rooms.")
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', type=int, default=8888)
    parser.add_argument('-m', '--maxconns', type=int, default=32)
    parser.add_argument('-l', '--messagelength', type=int, default=1024)
    args = parser.parse_args()

    allocator = PortAllocator(start_port=9000)
    daemon = TrackerDaemon(args.host, args.port, allocator, args.maxconns, args.messagelength)
    daemon.start()
