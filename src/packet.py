# Packet utilities
import argparse
import traceback
import sys
import socket
import struct
# Allows to store data received as a JSON, which we'll utilize to store in DB
import json
import time
from datetime import datetime

# SharedQueue buffer
from common import SharedQueue

# Log critical error events from SharedQueue wr/rd, Radio failures and Socket wr operations
import logging

# Multi-Threaded for Server and Radio operations
from threading import Lock
from threading import Thread

mutex = Lock()

# Global Logging Object
logging.basicConfig(filename="../log/rfserver.log", format='%(asctime)s %(message)s', filemode='a')
logger = logging.getLogger()


# Builds packet containing local hostname & port
# date and queue objects
def build_packet(hostname: str, port: int, Queue_Object: SharedQueue) -> bytes:

    # Encode for struct pack
    hostname_bytes = hostname.encode('utf-8')
    hostname_len   = len(hostname_bytes)

    # SharedQueue queue and item count
    queue        = Queue_Object.get_queue()
    queue_length = Queue_Object.get_count()

    cur_date = "{:%B %d %Y %H:%M:%S}".format(datetime.now())

    date_bytes = cur_date.encode('utf-8')
    date_len = len(date_bytes)

    # Packing format: Little Endian Hs[]HHs[]Hh[]
    packetformat = f'<H{hostname_len}sHH{date_len}sH{queue_length}h'

    packet = struct.pack(packetformat, 
                        hostname_len, hostname_bytes, 
                        port, 
                        date_len, date_bytes, 
                        queue_length, *queue)

    return packet


def unpack_packet(packet: bytes):
    
    print("Unpacking packet!")


    # Unpack hostname length
    hostname_len = struct.unpack_from('<H', packet, 0)[0]
    offset = 2

    # Unpack hostname
    hostname = struct.unpack_from(f'<{hostname_len}s', packet, offset)[0].decode('utf-8')
    offset += hostname_len

    # Unpack port
    port = struct.unpack_from('<H', packet, offset)[0]
    offset += 2

    # Unpack date length
    date_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2

    # Unpack date
    date = struct.unpack_from(f'<{date_len}s', packet, offset)[0].decode('utf-8')
    offset += date_len

    # Unpack queue length
    queue_length = struct.unpack_from('<H', packet, offset)[0]
    offset += 2

    # Unpack queue items
    queue = list(struct.unpack_from(f'<{queue_length}h', packet, offset))

    return {
        'hostname': hostname,
        'port': port,
        'date': date,
        'queue_length': queue_length,
        'queue': queue
    }







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
            logger.error(f"Error during RFPacketSender.connect(): {e}")

    # Safely close socket connection
    def close_socket(self):
        
        try:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
            self.client = None
        except Exception as e:
            logger.error(f"Error during RFPacketSender close_socket(): {e}")


    def send(self, packet : bytes):
        
        try:    
            if self.client is None or self.client.fileno() == -1:
                print("Socket is closed or invalid")
                return

            print(f"Sending packet len: {len(packet)} packet: {packet}")
            self.client.sendall(packet)
        except Exception as e:
            logger.error(f"Error during RFPacketSender.send(): {e}")


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
            logger.error(f"Error during RFPacketSender.send_iter(): {e}")


    def receive(self):

        try:
            recv = str(self.client.recv(1024), "utf-8")
            if recv:
                print(f"Received response: {recv}")

        except Exception as e:
            logger.error(f"Error during RFPacketSender.receive(): {e}")
            return None
