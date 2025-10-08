# https://docs.python.org/3/library/ctypes.html
import ctypes

# Incomplete Types ---- https://docs.python.org/3/library/ctypes.html#incomplete-types 
class packet(Structure):
    pass

packet._fields_ = [("header"), c_char_p,
                    ("body"), c_uint8,
                    ("body_len"), c_size_t,
                    ("date"), c_char_p
                ]

# Load C library
lib = ctypes.CDLL("./build/packet.so")

# Declaring argument and return types for the function(s)
lib.build_packet.argtypes = (ctypes.c_char, ctypes.c_char, ctypes.c_size_t)
lib.build_packet.restype = ctypes.c_uint8

def build_packet(header, body, packetlen):
    # Return Packet 
    return lib.build_packet(header, body, packetlen)


lib.unpack_packet.argtypes = (ctypes.uint8, ctypes.c_size_t)
lib.unpack_packet.restype = packet()

def unpack_packet(packet, packetlen):
    # Return bytes (struct packet)
    return lib.unpack_packet(packet, packetlen)