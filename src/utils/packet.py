# TODO: File sharing capabilities

# Packet utilities
import struct
# Allows to store data received as a JSON, which we'll utilize to store in DB
from datetime import datetime

# Log critical error events from wr/rd, Radio failures and Socket wr operations
import logging

# Global Logging Object
logging.basicConfig(filename="log/packet.log", format='%(asctime)s %(message)s', filemode='a')
logger = logging.getLogger()


# Builds packet, takes in username, message as parameters
# calls current time and packages/returns all as bytes
def build_packet(username: str, message: str) -> bytes:
    
    username_bytes = username.encode('utf-8')
    message_bytes = message.encode('utf-8')

    username_len = len(username_bytes)
    message_len = len(message_bytes)

    cur_date = "{:%B %d %Y %H:%M:%S}".format(datetime.now())
    cur_date_bytes = cur_date.encode('utf-8')
    cur_date_len = len(cur_date_bytes)

    packet_format = f'<H{username_len}sH{message_len}sH{cur_date_len}s'
    packet = struct.pack(
            packet_format,
            username_len, username_bytes,
            message_len, message_bytes,
            cur_date_len, cur_date_bytes)

    return packet


# Unpacks packet built by build_packet()
def unpack_packet(packet: bytes) -> dict:

    offset = 0

    # Unpack username
    username_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    username = struct.unpack_from(f'<{username_len}s', packet, offset)[0].decode('utf-8')
    offset += username_len

    # Unpack message
    message_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    message = struct.unpack_from(f'<{message_len}s', packet, offset)[0].decode('utf-8')
    offset += message_len

    # Unpack date
    date_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    date_str = struct.unpack_from(f'<{date_len}s', packet, offset)[0].decode('utf-8')

    return {
        'username': username,
        'message': message,
        'date': date_str
    }




#NOTE: Requires threading Thread
'''
# [THREAD] Producer: Builds packet frames from RF data
# The buffer will have an 'almost full' flag, where in >= %75
# of its size is reached will build the frame or if a certain
# amount of time has elapsed [30, 60] seconds and the buffer
# is not empty, will build the frame.
# Additionally, we'll keep track of the devices sending data dynamically
# Payload is in Queue Object

# Returns a struct pack containing local hostname, local port
# queue list and queue length
class PacketBuilder(Thread):

    def __init__(self, local_hostname: str, local_port: int):
        # Local Device
        self.local_hostname = local_hostname
        self.local_port = local_port

        # Thread Mutex thingamajig
        Thread.__init__(self)

    pass
    # Manage packets using packet.py

# Init should establish TCP connection, we'll simply send and await confirmation
class PacketSender(Thread):

    def __init__(self, remote_hostname: str, remote_port: int):        
        # Remote Device
        self.remote_hostname = remote_hostname
        self.remote_port = remote_port
        self.client = None

    # Connect to remote server
    def connect(self):

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connects client to server
            self.client.connect((self.remote_hostname, self.remote_port))
        
        except Exception as e:
            logger.error(f"Error during PacketSender.connect(): {e}")

    # Safely close socket connection
    def close_socket(self):
        
        try:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
            self.client = None
        except Exception as e:
            logger.error(f"Error during PacketSender close_socket(): {e}")


    def send(self, packet : bytes):
        
        try:    
            if self.client is None or self.client.fileno() == -1:
                print("Socket is closed or invalid")
                return

            print(f"Sending packet len: {len(packet)} packet: {packet}")
            self.client.sendall(packet)
        except Exception as e:
            logger.error(f"Error during PacketSender.send(): {e}")


    def send_iter(self, packet: bytes):

        try:
            if self.client is None or self.client.fileno() == -1:
                print("Socket is closed or invalid")
                return

            total_sent = 0
            while total_sent < len(packet):
                sent = self.client.send(packet[total_sent: ])
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent

            print(f"Sent {total_sent}/{len(packet)} bytes successfully: {packet}")

        except Exception as e:
            logger.error(f"Error during PacketSender.send_iter(): {e}")


    def receive(self):

        try:
            recv = str(self.client.recv(1024), "utf-8")
            if recv:
                print(f"Received response: {recv}")

        except Exception as e:
            logger.error(f"Error during PacketSender.receive(): {e}")
            return None
'''