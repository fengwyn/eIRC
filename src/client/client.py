# TODO: Encapsulate within classes, utilize the interface for swapping between IRC and Shell mode

# client: Contains modules for network communications into the server. Utilizes interface.rs for the shell mode and IRC mode interface.
import socket
import threading

try:
    # Choosing Username
    username = input("Choose your username: ")

    # Connecting To Server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('192.168.0.13', 8888))

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
                message = '{}: {}'.format(username, input(''))
                client.send(message.encode('ascii'))
            except KeyboardInterrupt:
                print("<KeyboardInterrupt>")
                client.shutdown()
                client.close()

    # Starting Threads For Listening And Writing
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()

except KeyboardInterrupt:
    print("<KeyboardInterrupt>")
    client.shutdown()
    client.close()
