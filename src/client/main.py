import argparse
import queue
import threading
from ..utils.interface import interface
from .client import Client

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="eIRC Client")
    parser.add_argument('-H', '--host', default='localhost', help='Tracker server hostname')
    parser.add_argument('-P', '--port', type=int, default=8888, help='Tracker server port')
    args = parser.parse_args()

    # Get username
    username = None
    while username is None:
        username = input("Choose your username: ").strip()
        if not username:
            print("Username cannot be empty.")

    # Create queues for communication between Interface and Client
    irc_command_queue = queue.Queue()
    client_response_queue = queue.Queue()

    # Initialize Client
    client = Client(args.host, args.port, username, use_queue=True)
    client.connect(args.host, args.port)

    # Initialize Interface with the command queue
    interface_thread = interface(irc_command_queue)

    # Start Client threads
    receive_thread = threading.Thread(target=client.receive, daemon=True)
    write_thread = threading.Thread(target=client.write, daemon=True)
    receive_thread.start()
    write_thread.start()

    # Main loop to handle communication between Interface and Client
    try:
        while True:
            # Check for IRC commands from Interface
            try:
                command = irc_command_queue.get_nowait()
                # If in IRC mode, send to Client's command queue
                if not interface_thread.in_shell_mode:
                    client.command_queue.put(command)
                # If in shell mode, handle shell commands locally
                else:
                    interface_thread.handle_shell_command(command)
            except queue.Empty:
                pass

            # Check for responses from Client
            try:
                response = client_response_queue.get_nowait()
                print(response)
            except queue.Empty:
                pass

    except KeyboardInterrupt:
        print("\nShutting down...")
        interface_thread.stop()
        client.stop()
        receive_thread.join()
        write_thread.join()
        interface_thread.join()

if __name__ == "__main__":
    main()
