#ifndef NODE_H
#define NODE_H

// node.h: C++ equivalent of server/server.py (class Server)
// TCP socket server for a single node room.
// Accepts client connections, handles message broadcasting,
// command routing (via CommandHandler), and client lifecycle.

#include <string>
#include <vector>
#include <unordered_set>
#include <mutex>
#include <cstdint>
#include <cstddef>

// Forward declarations
class NodeTracker;
class CommandHandler;


class Node {

private:

    // Server address
    std::string hostname;
    int port;

    // Limits
    int max_connections;
    int message_length;

    // Server socket file descriptor
    int server_fd;

    // Parallel arrays: clients[i] owns usernames[i]
    std::vector<int> clients;               // client socket fds
    std::vector<std::string> usernames;     // corresponding usernames
    std::mutex clients_mutex;               // protects both vectors

    // Valid command set (equivalent of get_commands() from interface.py)
    std::unordered_set<std::string> commands;

    // Node tracker instance (tracks active users, admins)
    NodeTracker *tracker;


    // --- Internal methods ---

    // Send raw bytes to every connected client
    void broadcast(const uint8_t *data, size_t len);

    // Per-client receive loop — runs in its own thread.
    // Unpacks packets, routes commands, relays whispers, broadcasts messages.
    void handle(int client_fd);

    // Accept loop — blocks forever, spawning a handle() thread per client.
    // Performs the USER handshake before handing off.
    void receive();

    // Remove a client from the room: close fd, erase from vectors,
    // broadcast leave message, deregister from tracker.
    void handle_client_leave(int client_fd);


public:

    Node(const std::string &hostname, int port,
         int max_connections, int message_length,
         const std::string &servername, const std::string &creatorname,
         const std::string &creatoraddr, bool is_private,
         const std::string &passkey);

    ~Node();

    // Calls listen() then enters the accept loop. Blocks until error/signal.
    void server_start();
};


#endif // NODE_H
