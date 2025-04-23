from server import Server

# Parameters:  ---hostname <address : Str> --port <port : int> --maxconns <max connections : int> --messagelength <message length: int>
# Running:      $ python3.13 server.py --hostname localhost --port 8888 --maxconns 32 --messagelength 64
if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser(prog="server.py", description="Listens to packets from RF Server nodes.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Server.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number for Server.")
    parser.add_argument('-m', '--maxconns', type=int, default=32, help="Maximum Server connections from clients.")
    parser.add_argument('-l', '--messagelength', type=int, default=128, help="Message length")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    maximum_connections = args.maxconns
    message_length = args.messagelength

    print(f"Host Server running at {socket.gethostbyname(hostname)}")

    print(f"Hostname: {hostname}, listening on port: {port}\
        \nMaximum connections {maximum_connections}, message length: {message_length}")

    server = Server(hostname, port, maximum_connections, message_length)
    server.server_start()
