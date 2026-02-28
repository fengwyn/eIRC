#ifndef NODE_COMMANDS_H
#define NODE_COMMANDS_H

// node_commands.h: C++ equivalent of server/node_commands.py
// CommandHandler routes node room commands (/users, /leave, /current, /whisper)
// to their handlers and returns built packets via the C packet API.

#include <string>
#include <vector>
#include <cstdint>
#include <cstddef>

// Forward declaration — full definition in utils/tracker.h
class NodeTracker;


// CommandHandler: allows node rooms to handle commands externally,
// so commands can be changed without rebooting the server.
//
// handle_command() returns a malloc'd packet buffer (caller must free)
// along with its length via out-param.  Returns nullptr for no response.
class CommandHandler {

private:

    NodeTracker *tracker;
    std::vector<std::string> *usernames;

    // Individual command handlers
    // Each returns a malloc'd packet (from build_packet), caller frees
    uint8_t* handle_users(size_t *packet_len);
    uint8_t* handle_leave(size_t *packet_len);
    uint8_t* handle_current(size_t *packet_len);
    uint8_t* handle_whisper(const std::string &command, size_t *packet_len);


public:

    CommandHandler(NodeTracker *tracker, std::vector<std::string> *usernames);

    // Routes command string to the appropriate handler.
    // Returns built packet (caller must free), or nullptr if unrecognized.
    // *packet_len is set to the byte count of the returned buffer.
    uint8_t* handle_command(const std::string &command, size_t *packet_len);
};


#endif // NODE_COMMANDS_H
