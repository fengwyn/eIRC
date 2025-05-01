# Run from project root:
#   $ ./eIRC/
#   $ python -m src.client.client

import socket
import threading
import errno    # Glorious UNIX error handling

from ..utils.packet import build_packet, unpack_packet

# Choosing Username
username = input("Choose your username: ")

# Connecting To Server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8888))


# Listening to Server and Sending Username
def receive():

    while True:
        try:
            packet = client.recv(1024)
            if not packet:
                print("Server closed the connection.")
                break

            # If the server literally says USER, send our username
            if packet == b'USER':
                client.send(username.encode('ascii'))
                
                continue

            # Otherwise, it's one of our structured packets
            try:
                read_packet = unpack_packet(packet)
                # Avoid shadowing the global `username` here:
                sender   = read_packet['username']
                body     = read_packet['message']
                datetime = read_packet['date']
                
                print(f"[{datetime}] {sender}: {body}")
                continue

            except Exception:
                # If the packet isn't our custom structured struct.pack,
                # then we'll fallback to plain-text control messages
                try:
                    notice = packet.decode('ascii').strip()
                    if notice:
                        print(notice)
                    
                    continue
                
                # Catch unknown binary blobs x)
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Exception: {e}")


        except Exception as e:
            print("Error in receive():", repr(e))
            break

    client.close()


# Sending Messages To Server
def write():

    while True:

        try:
            msg = input('')
            # Skip empty messages
            if not msg.strip():
                continue

            packet = build_packet(username, msg)

            try:
                client.send(packet)
            # This exception prevents the thing from exploding
            except OSError as sock_err:
                # EBADF (9) = Bad file descriptor, EPIPE (32) = Broken pipe
                if sock_err.errno in (errno.EBADF, errno.EPIPE):
                    print("Connection closed, writer exiting.")
                    break
                else:
                    raise

        except KeyboardInterrupt:

            print("\n<KeyboardInterrupt> Shutting down.")
            

            try:
                client.shutdown(socket.SHUT_RDWR)
            # This exception prevents the thing from exploding
            except OSError:
                pass
            client.close()
            break

        except Exception as e:
            print("Write error:", e)
            break


if __name__ == '__main__':
    # Start the listener and writer threads as daemons
    receive_thread = threading.Thread(target=receive, daemon=True)
    receive_thread.start()

    write_thread = threading.Thread(target=write, daemon=True)
    write_thread.start()

    # Keep the main thread alive until writer exits
    write_thread.join()
