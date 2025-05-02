# NOTE: Run as: python -m src.server.server --hostname localhost --port 8888 --maxconns 32 --messagelength 64
# This is so that we can utilize build_packet which is located in src/utils

# server: Handles socket server and implements socket communications between clients
# NOTE: https://docs.python.org/3.11/howto/sockets.html

import socketserver
import socket
import threading
import logging
import argparse
import time
from ..utils.packet import build_packet, unpack_packet


# Global Logging Object
logging.basicConfig(filename="log/server.log", format='%(asctime)s %(message)s', filemode='a')
logger = logging.getLogger()


# The connection will be TCP to ensure quality file wr/rd and content integrity
class Server(threading.Thread):

    def __init__(self, hostname, port, MAXIMUM_CONNECTIONS, MESSAGE_LENGTH):

        # Server Address
        self.hostname = hostname
        self.port     = port
        # Maximum connections and expected Message Length
        self.MAXIMUM_CONNECTIONS = MAXIMUM_CONNECTIONS
        self.MESSAGE_LENGTH = MESSAGE_LENGTH
        # Server socket initialization
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allows socket reuse address
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        time.sleep(0.5)
        self.server.bind((self.hostname, self.port))

        # Client addr and Client usr
        self.clients = []
        self.usernames = []


    # Sending Messages To All Connected Clients
    def broadcast(self, message):

        for client in self.clients:
            client.send(message)


    # TODO: If more than >1 user leaves, then have a counter
    # for which users incrementr when leaving, that will enable
    # the program to track them by using a list instead of a variable
    # and broadcast when they leave, instead of waiting for client action
    # At the moment, the client only knows when someone leaves when they send a message
    # Instead, we'll want the client leaving be broadcasted immediately
    # Handling Messages From Clients
    def handle(self, client):

        while True:
            
            try:
                # Broadcasting Messages
                # message = client.recv(1024)
                packet = bytes(client.recv(1024))

                # Unpack packet
                read_packet: dict() = unpack_packet(packet)
                header, body, date = read_packet['header'], read_packet['body'], read_packet['date']

                # The start of a message/body starts with '/' if it's a command
                if body[0] == '/':
                    print(f"Command: {body}")

                message = header + ': ' + body

                # print(message.decode('utf-8'))
                print(message)

                # Broadcast the message to everyone <sending the packet
                self.broadcast(packet)

            except:
                # Removing And Closing Clients
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                user = self.usernames[index]
                self.broadcast('{} left!'.format(user).encode('ascii'))
                self.usernames.remove(user)
                break


    # Receiving Function ---- The current implementation works by receiving when clients connect (verify)
    # NOTE: receiving and listen ARE different functionalities, see UNIX Socket Programming for more!
    def receive(self):
        
        while True:
            
            try:
                # Accept Connection
                client, address = self.server.accept()
                print("Connected with {}".format(str(address)))

                # Request And Store Username
                client.send('USER'.encode('ascii'))
                user = client.recv(1024).decode('ascii')
                self.usernames.append(user)
                self.clients.append(client)

                # Print And Broadcast Username
                print("Username is {}".format(user))
                self.broadcast("{} joined!".format(user).encode('ascii'))
                client.send('Connected to server!'.encode('ascii'))

                # Start Handling Thread For Client  (packets sent by clients are handled here)
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()
            
            except KeyboardInterrupt:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()

            except Exception as e:
                logger.error(f"Unhandled Exception during receive(): {e}")


    def server_start(self):

        try:
            self.server.listen()
            self.receive()

        except KeyboardInterrupt:

            logger.info("Manual Server Interrupt <KeyboardInterrupt>")
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.server_close()

        except Exception as e:
            logger.error(f"Error during server_start() excution: {e}")

# Parameters:  ---hostname <address : Str> --port <port : int> --maxconns <max connections : int> --messagelength <message length: int>
# Running:      $ python3.13 server.py --hostname localhost --port 8888 --maxconns 32 --messagelength 64
if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog="server.py", description="Chat Room Server")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Server")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number for Server")
    parser.add_argument('-m', '--maxconns', type=int, default=32, help="Maximum Server connections from clients")
    parser.add_argument('-l', '--messagelength', type=int, default=128, help="Message length")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    maximum_connections = args.maxconns
    message_length = args.messagelength

    print(f"Host Server running at {socket.gethostbyname(hostname)}")

    print(f"Hostname: {hostname}, listening on port: {port}\
        \nMaximum connections {maximum_connections}, message length: {message_length}")

    server = Server(hostname, port, maximum_connections, message_length)
    server.server_start()
