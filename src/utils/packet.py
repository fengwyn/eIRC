# Packet utilities
import struct
from datetime import datetime

# Log critical error events from wr/rd
import logging

# Global Logging Object
logging.basicConfig(filename="log/packet.log", format='%(asctime)s %(body)s', filemode='a')
logger = logging.getLogger()


# Builds packet, takes in header, body as parameters
# calls current time and packages/returns all as bytes
def build_packet(header: str, body: str) -> bytes:
    
    header_bytes = header.encode('utf-8')
    body_bytes = body.encode('utf-8')

    header_len = len(header_bytes)
    body_len = len(body_bytes)

    cur_date = "{:%B %d %Y %H:%M:%S}".format(datetime.now())
    cur_date_bytes = cur_date.encode('utf-8')
    cur_date_len = len(cur_date_bytes)

    packet_format = f'<H{header_len}sH{body_len}sH{cur_date_len}s'
    packet = struct.pack(
            packet_format,
            header_len, header_bytes,
            body_len, body_bytes,
            cur_date_len, cur_date_bytes)

    return packet


# Unpacks packet built by build_packet()
def unpack_packet(packet: bytes) -> dict:

    offset = 0

    # Unpack header
    header_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    header = struct.unpack_from(f'<{header_len}s', packet, offset)[0].decode('utf-8')
    offset += header_len

    # Unpack body
    body_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    body = struct.unpack_from(f'<{body_len}s', packet, offset)[0].decode('utf-8')
    offset += body_len

    # Unpack date
    date_len = struct.unpack_from('<H', packet, offset)[0]
    offset += 2
    date_str = struct.unpack_from(f'<{date_len}s', packet, offset)[0].decode('utf-8')

    return {
        'header': header,
        'body': body,
        'date': date_str
    }