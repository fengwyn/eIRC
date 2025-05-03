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

                        case "/create":

                            if len(args) < 2:
                                packet = build_packet("ERROR Usage", "/create <name> <admin_user>")
                                conn.send(packet)
                                continue
                            
                            name = args[0]
                            admin_user = args[1]

                            # allocate a port for new chat server
                            chat_port = self.allocator.allocate()

                            # start chat server instance
                            chat_srv = ChatRoomServer(self.host, chat_port, self.max_conns, self.msg_length)
                            threading.Thread(target=chat_srv.server_start, daemon=True).start()

                            # register in tracker
                            admin_address = f"{addr[0]}:{addr[1]}"
                            self.tracker.register_server(
                                name,
                                f"{self.host}:{chat_port}",
                                admin_user=admin_user,
                                admin_address=admin_address,
                                is_private=False,
                                passkey=""
                            )

                            packet = build_packet("CHAT CREATED", f"{name} {self.host} {chat_port}")
                            conn.send(packet)

                        case "/list":

                            servers = self.tracker.get_server_list()
                            resp = "ACTIVE_SERVERS\n"
                            for sname, saddr in servers.items():
                                resp += f"{sname} @ {saddr}\n"

                            packet = build_packet("/list", resp)
                            conn.send(packet)


                        case "/join":

                            if len(args) < 1:
                                packet = build_packet("ERROR Usage", "/join <name>")
                                conn.send(packet)
                                continue
                        
                            name = args[0]
                            servers = self.tracker.get_server_list()    # <- This is a dict()
                            
                            if name in servers:

                                packet = build_packet("JOIN", f"{servers[name]}")
                                print(f"JOIN: {servers[name]} @ {servers[name]}")
                                conn.send(packet)

                            else:
                                packet = build_packet("ERROR", "Server not found")
                                conn.send(packet)


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
