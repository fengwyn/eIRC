# Run from project root:
#   $ python -m src.client.client

import argparse
import socket
import threading
import errno    # UNIX error codes
from ..utils.packet import build_packet, unpack_packet


class Client(threading.Thread):

    def __init__(self, hostname, port, username):
        super().__init__()
        # Threaded socket lock
        self.client_lock = threading.Lock()

        self.client = None
        self.username = username
        self.hostname = hostname
        self.port = port

        self.tracker_addr = hostname
        self.tracker_port = port


    # Used for reconnecting to new server
    def connect(self, addr, port):
        # Check if already have a client socket
        with self.client_lock:
            if self.client:
                # First close the connection
                try:
                    self.client.close()
                except:
                    pass

            # Now connect to new server
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((addr, port))
            print(f"Connected to {addr}:{port}")


    def receive(self):

        while True:

            try:
                packet = self.client.recv(1024)

                if not packet:
                    print("Server closed the connection.")
                    break

                # SERVER: handshake prompt?
                if packet == b'USER':
                    self.client.send(self.username.encode('ascii'))
                    continue

                # Structured packet
                try:
                    p = unpack_packet(packet)
                    sender = p['header']
                    body   = p['body']
                    date   = p['date']
                    print(f"[{date}] {sender}: {body}")

                    # NOTE: Some commands must be handled client-side, 
                    # such as hopping into a new chat room, leaving a chat room,
                    # exiting the client, and otherwise all other which relies on the client socket fd.
                    match sender:

                        # Auto hop on CHAT CREATED
                        case "CHAT CREATED":
                            # body == "<room> <host> <port>"
                            room, host, port_s = body.split()
                            port = int(port_s)
                            print(f"Hopping into new chat `{room}` @ {host}:{port}…")
                            # Reconnect
                            self.connect(host, port)
                            # No immediate username send here yet,
                            # now we'll wait for the b'USER' prompt
                            continue


                        case "WHISPER":
                            # Whisper messages are already formatted in the body
                            print(f"\n[WHISPER] {body}\n")
                            continue


                        case "JOIN":
                            ip, port = body.split(':')
                            port = int(port)
                            print(f"Joining chat server @{body}")
                            self.connect(ip, port)

                        # NOTE: LEAVE is when leaving a chat room, which hops back into a tracker
                        # EXIT is for leaving the tracker and ultimately the master server
                        case "LEAVE":
                            print("Leaving chat room...\nRedirecting to known tracker(s).")
                            self.connect(self.tracker_addr, self.tracker_port)
                        
                        case "EXIT":
                            print("Goodbye!")
                            with self.client_lock:
                                self.client.close()
                            # Go back to interface mode

                        # NOTE: Literally all other packets are passed through here
                        case _:
                            # print("Handling unknown packet...")
                            pass

                except Exception:
                    # fallback to plain-text
                    text = packet.decode('ascii', errors='ignore').strip()
                    if text:
                        print(text)
                    continue

            except Exception as e:
                print("Error in receive():", e)
                break

        with self.client_lock:
            self.client.close()



    def write(self):

        while True:

            try:
                msg = input()

                if not msg.strip():
                    continue

                packet = build_packet(self.username, msg)
                self.client.send(packet)


            except KeyboardInterrupt:
                print("\n<KeyboardInterrupt> Shutting down.")
                try:
                    self.client.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.client.close()
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

    parser = argparse.ArgumentParser(description="Tracker Server address")
    parser.add_argument('-H', '--host',  default='localhost')
    parser.add_argument('-P', '--port',  type=int, default=8888)
    args = parser.parse_args()

    username = None
    while username is None:
        username = input("Choose your username: ").strip()
        if not username:
            print("Username cannot be empty.")

    client = Client(args.host, args.port, username)

    # Initial connect to tracker
    client.connect(args.host, args.port)

    threading.Thread(target=client.receive, daemon=True).start()
    threading.Thread(target=client.write, daemon=True).start()
    # Keep main alive
    threading.Event().wait()
