#NOTE: Run from project root: $ ./eIRC/ then: $ python -m src.client.client
# This is so that we can utilize build_packet which is located in src/utils

# TODO: Encapsulate within classes, utilize the interface for swapping between IRC and Shell mode

# client: Contains modules for network communications into the server. Utilizes interface.rs for the shell mode and IRC mode interface.
import socket
import threading


from ..utils.packet import build_packet

try:
    # Choosing Username
    username = input("Choose your username: ")

    # Connecting To Server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 8888))

    # Listening to Server and Sending Username
    def receive():

        while True:
            try:
                # Receive Message From Server
                # If 'USER' Send Username
                message = client.recv(1024).decode('ascii')
                if message == 'USER':
                    client.send(username.encode('ascii'))
                else:
                    print(message)
            except:
                # Close Connection When Error
                print("An error occured!")
                client.close()
                break

    # Sending Messages To Server
    def write():

        while True:        
            try:
                try:
                    message = input('')                
                    # If message starts with '/' then it's a command
                    # structured as <Command>:<Username>
                    # This will make it easier on the server side to manage
                    if message[0] == '/':
                        message = '{}:{}'.format(message, username)
                    else:
                        message = '{}:{}'.format(username, message)

                    # message = '{}: {}'.format(username, input(''))
                    client.send(message.encode('ascii'))
            
                # Ctrl+C
                except KeyboardInterrupt:
                    print("<KeyboardInterrupt>")
                    client.shutdown()
                    client.close()

            # Handle unknown exception
            except Exception as e:
                pass

    # Starting Threads For Listening And Writing
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()

except KeyboardInterrupt:
    print("<KeyboardInterrupt>")
    client.shutdown()
    client.close()
