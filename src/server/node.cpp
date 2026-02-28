// node.cpp: C++ equivalent of server/server.py
// TCP node room server — one thread per connected client.
//
// Build (example):
//   g++ -std=c++17 -pthread -o node node.cpp ../utils/packet.c \
//       [tracker.o] [node_commands.o] -I../utils -I.
//
// Run (standalone):
//   ./node -H localhost -P 8888 -m 32 -l 128 \
//          -n "room" -c "admin" -a "127.0.0.1:9999" -i 0 -p ""

#include "node.h"
#include "node_commands.h"
#include "../utils/tracker.h"

// C packet API — needs extern "C" to prevent C++ name mangling
#include <cstdint>
#include <cstddef>
extern "C" {
    #include "../utils/packet.h"
    // free_packet_data is defined in packet.c but not declared in packet.h
    extern void free_packet_data(PacketData *data);
}

// Standard library
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <unordered_set>
#include <thread>
#include <mutex>

// POSIX sockets
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

// Logging (placeholder — mirrors Python's logging.basicConfig)
#include <cstdarg>
static void log_error(const char *fmt, ...) {
    // TODO: integrate with log/server.log file logger
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");
}


// ---------------------------------------------------------------------------
// Equivalent of: from ..utils.interface import get_commands
// Returns the set of valid IRC command strings recognised by the node server.
// ---------------------------------------------------------------------------
static std::unordered_set<std::string> get_commands() {

    return {
        "/sh", "/irc", "/servers", "/users", "/current", "/whisper",
        "/join", "/accept", "/reject", "/leave", "/delete",
        "/sendfile", "/receivefile", "/exit", "/off", "/commands"
    };
}


// ---------------------------------------------------------------------------
// Helper: split a string by whitespace, up to `max_splits` pieces.
// Mirrors Python str.split(maxsplit=N).
// ---------------------------------------------------------------------------
static std::vector<std::string> split(const std::string &s, size_t max_splits = (size_t)-1) {

    std::vector<std::string> tokens;
    size_t start = 0;
    size_t splits = 0;

    while (start < s.size()) {
        // skip leading spaces
        while (start < s.size() && s[start] == ' ') start++;
        if (start >= s.size()) break;

        if (splits >= max_splits) {
            // rest of string is the final token
            tokens.push_back(s.substr(start));
            break;
        }

        size_t end = s.find(' ', start);
        if (end == std::string::npos) {
            tokens.push_back(s.substr(start));
            break;
        }

        tokens.push_back(s.substr(start, end - start));
        start = end + 1;
        splits++;
    }

    return tokens;
}


// ===========================================================================
//  Node constructor
// ===========================================================================

Node::Node(const std::string &hostname, int port,
           int max_connections, int message_length,
           const std::string &servername, const std::string &creatorname,
           const std::string &creatoraddr, bool is_private,
           const std::string &passkey)
    : hostname(hostname)
    , port(port)
    , max_connections(max_connections)
    , message_length(message_length)
    , server_fd(-1)
    , tracker(nullptr)
{
    // --- Create TCP socket ---
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return;
    }

    // SO_REUSEADDR — allows immediate rebind after restart
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // --- Bind ---
    struct sockaddr_in addr{};
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(port);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        server_fd = -1;
        return;
    }

    // --- Valid command set ---
    commands = get_commands();

    // --- Node tracker (tracks users in this room) ---
    std::string node_address = hostname + ":" + std::to_string(port);
    tracker = new NodeTracker(servername, node_address,
                              creatorname, creatoraddr,
                              is_private, passkey);
}


Node::~Node() {

    if (server_fd >= 0) {
        close(server_fd);
    }

    // Close all client sockets
    std::lock_guard<std::mutex> guard(clients_mutex);
    for (int fd : clients) {
        close(fd);
    }
    clients.clear();
    usernames.clear();

    delete tracker;
}


// ===========================================================================
//  broadcast — send raw bytes to every connected client
// ===========================================================================

void Node::broadcast(const uint8_t *data, size_t len) {

    std::lock_guard<std::mutex> guard(clients_mutex);
    for (int fd : clients) {
        ::send(fd, data, len, 0);
    }
}


// ===========================================================================
//  handle_client_leave — remove a client from the room
// ===========================================================================

void Node::handle_client_leave(int client_fd) {

    std::string user;

    // --- Critical section: remove from vectors ---
    {
        std::lock_guard<std::mutex> guard(clients_mutex);

        // Find the client's index
        int index = -1;
        for (size_t i = 0; i < clients.size(); i++) {
            if (clients[i] == client_fd) {
                index = (int)i;
                break;
            }
        }

        if (index < 0) return;     // already removed

        user = usernames[index];
        clients.erase(clients.begin() + index);
        usernames.erase(usernames.begin() + index);
    }
    // --- End critical section ---

    close(client_fd);

    // Broadcast leave message (raw ASCII, matches Python behaviour)
    std::string leave_msg = user + " left!";
    broadcast((const uint8_t *)leave_msg.c_str(), leave_msg.size());

    // Deregister from tracker
    tracker->user_leave(user);

    printf("%s left the room.\n", user.c_str());
}


// ===========================================================================
//  handle — per-client receive loop (runs in its own thread)
// ===========================================================================

void Node::handle(int client_fd) {

    // One CommandHandler per client thread (mirrors Python)
    CommandHandler cmd_handler(tracker, &usernames);

    uint8_t buf[1024];

    while (true) {

        ssize_t n = recv(client_fd, buf, sizeof(buf), 0);
        if (n <= 0) {
            // Connection closed or error — treat as leave
            handle_client_leave(client_fd);
            return;
        }

        // --- Unpack the structured packet ---
        PacketData *pkt = unpack_packet(buf, (size_t)n);
        if (!pkt) {
            handle_client_leave(client_fd);
            return;
        }

        std::string header(pkt->header);
        std::string body((const char *)pkt->body, pkt->body_len);
        // date available as pkt->date if needed
        free_packet_data(pkt);


        // --- Command handling (body starts with '/') ---
        if (!body.empty() && body[0] == '/') {

            printf("Command: %s\n", body.c_str());

            if (body.size() < 2) continue;

            // Base command is the first whitespace-delimited token
            std::string base_command = split(body, 1)[0];

            if (commands.find(base_command) == commands.end()) {
                printf("Invalid Command: %s\n", base_command.c_str());
                continue;
            }

            // Route through CommandHandler
            size_t resp_len = 0;
            uint8_t *response = cmd_handler.handle_command(body, &resp_len);

            if (response) {

                // --- /whisper: relay to target, confirm to sender ---
                if (base_command == "/whisper") {

                    PacketData *wpkt = unpack_packet(response, resp_len);

                    if (wpkt && std::string(wpkt->header) == "WHISPER") {

                        std::string wbody((const char *)wpkt->body, wpkt->body_len);
                        // body format: "target_user|message"
                        size_t pipe = wbody.find('|');

                        if (pipe != std::string::npos) {

                            std::string target_user = wbody.substr(0, pipe);
                            std::string message     = wbody.substr(pipe + 1);

                            // Find target client fd
                            int target_fd = -1;
                            {
                                std::lock_guard<std::mutex> guard(clients_mutex);
                                for (size_t i = 0; i < usernames.size(); i++) {
                                    if (usernames[i] == target_user) {
                                        target_fd = clients[i];
                                        break;
                                    }
                                }
                            }

                            if (target_fd >= 0) {
                                // Send whisper to target
                                std::string whisper_msg = "Whisper from " + header + ": " + message;
                                size_t plen = 0;
                                uint8_t *wpk = build_packet("WHISPER", whisper_msg.c_str(), &plen);
                                if (wpk) {
                                    ::send(target_fd, wpk, plen, 0);
                                    free(wpk);
                                }

                                // Confirmation to sender
                                std::string confirm = "Whisper sent to " + target_user;
                                uint8_t *cpk = build_packet("WHISPER", confirm.c_str(), &plen);
                                if (cpk) {
                                    ::send(client_fd, cpk, plen, 0);
                                    free(cpk);
                                }
                            }
                        }
                        // Pipe not found — this is an error packet, send to sender
                        else {
                            ::send(client_fd, response, resp_len, 0);
                        }

                        if (wpkt) free_packet_data(wpkt);

                    } else {
                        // Header != "WHISPER" — error response, send to sender
                        ::send(client_fd, response, resp_len, 0);
                        if (wpkt) free_packet_data(wpkt);
                    }
                }

                // --- /leave: send response then disconnect ---
                else if (base_command == "/leave") {
                    ::send(client_fd, response, resp_len, 0);
                    free(response);
                    handle_client_leave(client_fd);
                    return;
                }

                // --- Default: send response back to sender ---
                else {
                    ::send(client_fd, response, resp_len, 0);
                }

                free(response);
            }
            // No response from handler — continue
            continue;
        }


        // --- Regular message: print and broadcast ---
        std::string display = header + ": " + body;
        printf("%s\n", display.c_str());

        // Broadcast the original raw packet bytes to all clients
        broadcast(buf, (size_t)n);
    }
}


// ===========================================================================
//  receive — accept loop with USER handshake
// ===========================================================================

void Node::receive() {

    while (true) {

        struct sockaddr_in client_addr{};
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &addr_len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        char addr_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, addr_str, sizeof(addr_str));
        printf("Connected with %s:%d\n", addr_str, ntohs(client_addr.sin_port));


        // --- USER handshake (raw ASCII, not a structured packet) ---
        const char *prompt = "USER";
        ::send(client_fd, prompt, strlen(prompt), 0);

        char user_buf[1024]{};
        ssize_t ulen = recv(client_fd, user_buf, sizeof(user_buf) - 1, 0);
        if (ulen <= 0) {
            close(client_fd);
            continue;
        }
        user_buf[ulen] = '\0';
        std::string user(user_buf);


        // --- Register client ---
        {
            std::lock_guard<std::mutex> guard(clients_mutex);
            clients.push_back(client_fd);
            usernames.push_back(user);
        }

        // Register in node tracker
        std::string user_address = std::string(addr_str) + ":" + std::to_string(ntohs(client_addr.sin_port));
        tracker->add_member(user, user_address);

        // Broadcast join (raw ASCII, matches Python)
        printf("Username is %s\n", user.c_str());
        std::string join_msg = user + " joined!";
        broadcast((const uint8_t *)join_msg.c_str(), join_msg.size());

        // Welcome the client (raw ASCII)
        const char *welcome = "Connected to server!";
        ::send(client_fd, welcome, strlen(welcome), 0);


        // --- Spawn handler thread (detached, mirrors Python daemon=True) ---
        std::thread(&Node::handle, this, client_fd).detach();
    }
}


// ===========================================================================
//  server_start — listen then enter accept loop
// ===========================================================================

void Node::server_start() {

    if (server_fd < 0) {
        log_error("server_start: invalid socket, cannot listen");
        return;
    }

    if (listen(server_fd, max_connections) < 0) {
        perror("listen");
        return;
    }

    printf("Node server listening on %s:%d\n", hostname.c_str(), port);
    receive();
}


// ===========================================================================
//  main — standalone driver (mirrors __main__ in server.py)
// ===========================================================================

int main(int argc, char **argv) {

    // Defaults matching server.py argparse
    std::string hostname    = "localhost";
    int port                = 8888;
    int maxconns            = 32;
    int messagelength       = 128;
    std::string servername  = "";
    std::string creatorname = "";
    std::string creatoraddr = "";
    bool is_private         = false;
    std::string passkey     = "";

    // Minimal getopt-style argument parsing
    // Usage: ./node -H <host> -P <port> -m <maxconns> -l <msglen>
    //               -n <name> -c <creator> -a <addr> -i <0|1> -p <key>
    for (int i = 1; i < argc; i++) {

        std::string arg(argv[i]);

        if ((arg == "-H" || arg == "--hostname") && i + 1 < argc)
            hostname = argv[++i];
        else if ((arg == "-P" || arg == "--port") && i + 1 < argc)
            port = std::atoi(argv[++i]);
        else if ((arg == "-m" || arg == "--maxconns") && i + 1 < argc)
            maxconns = std::atoi(argv[++i]);
        else if ((arg == "-l" || arg == "--messagelength") && i + 1 < argc)
            messagelength = std::atoi(argv[++i]);
        else if ((arg == "-n" || arg == "--servername") && i + 1 < argc)
            servername = argv[++i];
        else if ((arg == "-c" || arg == "--creatorname") && i + 1 < argc)
            creatorname = argv[++i];
        else if ((arg == "-a" || arg == "--creatoraddr") && i + 1 < argc)
            creatoraddr = argv[++i];
        else if ((arg == "-i" || arg == "--isPrivate") && i + 1 < argc)
            is_private = (std::atoi(argv[++i]) != 0);
        else if ((arg == "-p" || arg == "--passkey") && i + 1 < argc)
            passkey = argv[++i];
    }

    printf("Hostname: %s, listening on port: %d\n"
           "Maximum connections %d, message length: %d\n"
           "Server name: %s, creator name: %s, creator address: %s\n"
           "Is private: %d, passkey: %s\n",
           hostname.c_str(), port,
           maxconns, messagelength,
           servername.c_str(), creatorname.c_str(), creatoraddr.c_str(),
           is_private ? 1 : 0, passkey.c_str());

    Node node(hostname, port, maxconns, messagelength,
              servername, creatorname, creatoraddr, is_private, passkey);

    node.server_start();

    return 0;
}
