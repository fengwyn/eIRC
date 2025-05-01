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