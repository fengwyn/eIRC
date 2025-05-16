# Run from project root:
#   $ python -m src.client.client

import argparse
import socket
import threading
import errno    # UNIX error codes
from ..utils.packet import build_packet, unpack_packet



# Threaded socket lock
client_lock = threading.Lock()

client = None
username = None

tracker_addr = None
tracker_port = None

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
    # Used for reconnecting to tracker after leaving a chat room
    global tracker_addr, tracker_port

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
                date   = p['date']
                print(f"[{date}] {sender}: {body}")


                match sender:

                    # Auto hop on CHAT CREATED
                    case "CHAT CREATED":
                        # body == "<room> <host> <port>"
                        room, host, port_s = body.split()
                        port = int(port_s)
                        print(f"Hopping into new chat `{room}` @ {host}:{port}…")
                        # Reconnect
                        connect(host, port)
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
                        connect(ip, port)


                    # NOTE: LEAVE is when leaving a chat room, which hops back into a tracker
                    # EXIT is for leaving the tracker and ultimately the master server
                    case "LEAVE":
                        print("Leaving chat room...\nRedirecting to known tracker(s).")
                        connect(tracker_addr, tracker_port)
                    
                    # NOTE: So far, this'll close the client write, but not receive
                    # Since we still want to stay inside the eIRC interface,
                    # we must simply destroy or freeze (whichever is implemented)
                    # the Client Class object instance (and its thread)

                    # If the user wants to reinitiate another connection, then the Client object
                    # should once again be instantiated
                    case "EXIT":
                        print("Goodbye!")
                        with client_lock:
                            client.close()
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


            # Some commands must be handled by special cases, such as exit and file sending
            # if msg.startswith('/'):
                
            #     match msg:

            #         case "/leave":
            #             pass

            #         case "/exit":
            #             packet = build_packet(username, msg)

            #         case _:
            #             print(f"Command : {msg} not handled...")
                # eo match
            # eo if

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

    parser = argparse.ArgumentParser(description="Tracker Server address")
    parser.add_argument('-H', '--host',  default='localhost')
    parser.add_argument('-P', '--port',  type=int, default=8888)
    args = parser.parse_args()

    username = None
    # We must have a living initiated instance of the tracker address such as to hop back during LEAVE
    tracker_addr = args.host
    tracker_port = args.port

    while username is None:
        username = input("Choose your username: ").strip()
        if not username:
            print("Username cannot be empty.")

    # Initial connect to tracker
    connect(args.host, args.port)

    threading.Thread(target=receive, daemon=True).start()
    threading.Thread(target=write, daemon=True).start()
    # Keep main alive
    threading.Event().wait()
