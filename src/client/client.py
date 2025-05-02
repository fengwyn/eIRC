# Run from project root:
#   $ python -m src.client.client

import socket
import threading
import errno    # UNIX error codes
from ..utils.packet import build_packet, unpack_packet



# Threaded socket lock
client_lock = threading.Lock()

client = None
username = None

# Used for reconnecting to new server
def connect(addr, port):

    global client

    # Check if already have a client socket
    with client_lock:
        if client:
            # First close the connection
            try:
                client.close()
            except:
                pass

        # Now connect to new server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((addr, port))
        print(f"Connected to {addr}:{port}")


def receive():

    global client, username

    while True:

        try:
            packet = client.recv(1024)

            if not packet:
                print("Server closed the connection.")
                break

            # SERVER: handshake prompt?
            if packet == b'USER':
                client.send(username.encode('ascii'))
                continue

            # Structured packet
            try:
                p = unpack_packet(packet)
                sender = p['header']
                body   = p['body']
                date     = p['date']
                print(f"[{date}] {sender}: {body}")

                # Auto hop on CHAT CREATED
                if sender == "CHAT CREATED":
                    # body == "<room> <host> <port>"
                    room, host, port_s = body.split()
                    port = int(port_s)
                    print(f"> Hopping into new chat `{room}` @ {host}:{port}…")
                    # Reconnect
                    connect(host, port)
                    # No immediate username send here yet,
                    # now we'll wait for the b'USER' prompt.
                    continue

            except Exception:
                # fallback to plain-text
                text = packet.decode('ascii', errors='ignore').strip()
                if text:
                    print(text)
                continue

        except Exception as e:
            print("Error in receive():", e)
            break
    # eo while true

    # if client:
    #     client.close()
    with client_lock:
        client.close()


def write():

    global client

    while True:

        try:
            msg = input()

            if not msg.strip():
                continue

            packet = build_packet(username, msg)
            client.send(packet)

        except KeyboardInterrupt:

            print("\n<KeyboardInterrupt> Shutting down.")

            try:
                client.shutdown(socket.SHUT_RDWR)
            except:
                pass

            client.close()
            break

        except OSError as sock_err:

            if sock_err.errno in (errno.EBADF, errno.EPIPE):
                print("Connection closed, writer exiting.")
                break

            else:
                raise

        except Exception as e:
            print("Write error:", e)
            break



if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Tracker Server address")
    parser.add_argument('-H', '--host',  default='localhost')
    parser.add_argument('-P', '--port',  type=int, default=8888)
    args = parser.parse_args()

    username = input("Choose your username: ").strip()
    if not username:
        print("Username cannot be empty.")
        exit(1)

    # Initial connect to tracker
    connect(args.host, args.port)

    threading.Thread(target=receive, daemon=True).start()
    threading.Thread(target=write, daemon=True).start()
    # Keep main alive
    threading.Event().wait()
