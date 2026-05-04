#ifndef NODE_COMMANDS_H
#define NODE_COMMANDS_H

// node_commands.h: C++ equivalent of server/node_commands.py
// CommandHandler routes node room commands (/users, /leave, /current,
// /whisper, /oselot) to their handlers and returns built packets via
// the C packet API.

#include <string>
#include <vector>
#include <deque>
#include <mutex>
#include <cstdint>
#include <cstddef>

// Forward declaration — full definition in utils/tracker.h
class NodeTracker;


// One [OSELOT] metadata event recorded by the node.
struct OselotEvent {
    std::string nick;   // server-authoritative sender nick (oselot*)
    std::string line;   // full payload as received, beginning "[OSELOT] "
};


// OselotState
// Shared per-Node ring buffer of the most recent [OSELOT] metadata lines.
// Late-joining clients query it via /oselot status and /oselot history.
// Thread-safe.
//
// [OSELOT-XFER] chunked-transfer lines are NOT stored here — they are
// broadcast unchanged and reassembled by an external receiver
// (irc_chunked_receiver.py connected as a regular client).
//
// (1c) follow-up: when server-side reassembly + /oselot files lands,
// extend this class with an in-flight transfer table and a saved-files
// index.
class OselotState {

public:

    static constexpr size_t MAX_HISTORY = 10;

    void record(const std::string &nick, const std::string &line);
    std::vector<OselotEvent> recent(size_t n) const;
    bool empty() const;

private:

    mutable std::mutex mtx;
    std::deque<OselotEvent> buffer;
};


// CommandHandler: allows node rooms to handle commands externally,
// so commands can be changed without rebooting the server.
//
// handle_command() returns a malloc'd packet buffer (caller must free)
// along with its length via out-param.  Returns nullptr for no response.
class CommandHandler {

private:

    NodeTracker *tracker;
    std::vector<std::string> *usernames;
    OselotState *oselot;

    // Individual command handlers
    // Each returns a malloc'd packet (from build_packet), caller frees
    uint8_t* handle_users(size_t *packet_len);
    uint8_t* handle_leave(size_t *packet_len);
    uint8_t* handle_current(size_t *packet_len);
    uint8_t* handle_whisper(const std::string &command, size_t *packet_len);

    // /oselot subcommand router and handlers
    uint8_t* handle_oselot(const std::string &command, size_t *packet_len);
    uint8_t* handle_oselot_status(size_t *packet_len);
    uint8_t* handle_oselot_history(size_t n, size_t *packet_len);

    // Placeholder for the (1c) follow-up: live progress of an in-flight
    // [OSELOT-XFER]. Returns "not implemented" today; wire it up once
    // OselotState gains an in-flight transfer table.
    uint8_t* handle_oselot_xfer(size_t *packet_len);


public:

    CommandHandler(NodeTracker *tracker,
                   std::vector<std::string> *usernames,
                   OselotState *oselot);

    // Routes command string to the appropriate handler.
    // Returns built packet (caller must free), or nullptr if unrecognized.
    // *packet_len is set to the byte count of the returned buffer.
    uint8_t* handle_command(const std::string &command, size_t *packet_len);
};


#endif // NODE_COMMANDS_H
