// node_commands.cpp: C++ equivalent of server/node_commands.py
// CommandHandler routes node room commands to their handler functions
// and returns built packets via the C packet API.
//
// This mirrors the Python pattern where each command maps to a handler,
// allowing commands to be added/changed without rebooting the server.

#include "node_commands.h"
#include "../utils/tracker.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>

// C packet API
#include <cstdint>
#include <cstddef>
extern "C" {
    #include "../utils/packet.h"
}


// ===========================================================================
//  Constructor
// ===========================================================================

CommandHandler::CommandHandler(NodeTracker *tracker, std::vector<std::string> *usernames)
    : tracker(tracker)
    , usernames(usernames)
{
}


// ===========================================================================
//  handle_command — routes command string to the appropriate handler
//  Returns malloc'd packet (caller must free), or nullptr if unrecognized.
// ===========================================================================

uint8_t* CommandHandler::handle_command(const std::string &command, size_t *packet_len) {

    *packet_len = 0;

    if (command.empty() || command[0] != '/') {
        return nullptr;
    }

    // Strip leading/trailing whitespace
    size_t start = command.find_first_not_of(' ');
    size_t end   = command.find_last_not_of(' ');
    std::string trimmed = command.substr(start, end - start + 1);

    // Extract base command (first whitespace-delimited token)
    size_t space_pos = trimmed.find(' ');
    std::string base_command = (space_pos != std::string::npos)
        ? trimmed.substr(0, space_pos)
        : trimmed;

    // Route to handler — mirrors the Python dict dispatch
    if (base_command == "/users") {
        return handle_users(packet_len);
    }
    if (base_command == "/leave") {
        return handle_leave(packet_len);
    }
    if (base_command == "/current") {
        return handle_current(packet_len);
    }
    if (base_command == "/whisper") {
        return handle_whisper(trimmed, packet_len);
    }

    // Unrecognized command
    return nullptr;
}


// ===========================================================================
//  /users — returns comma-separated list of connected usernames
// ===========================================================================

uint8_t* CommandHandler::handle_users(size_t *packet_len) {

    std::string user_list;

    for (size_t i = 0; i < usernames->size(); i++) {
        if (i > 0) user_list += ", ";
        user_list += (*usernames)[i];
    }

    return build_packet("Users", user_list.c_str(), packet_len);
}


// ===========================================================================
//  /leave — builds a LEAVE packet (actual disconnect is handled by Node)
// ===========================================================================

uint8_t* CommandHandler::handle_leave(size_t *packet_len) {

    return build_packet("LEAVE", "Leaving node room...", packet_len);
}


// ===========================================================================
//  /current — returns the name of this node room
// ===========================================================================

uint8_t* CommandHandler::handle_current(size_t *packet_len) {

    std::string srv_name = tracker->get_name();
    return build_packet("Currently in:", srv_name.c_str(), packet_len);
}


// ===========================================================================
//  /whisper — builds a WHISPER packet with "target_user|message" body
//  The actual relay to the target client is handled by Node::handle().
// ===========================================================================

uint8_t* CommandHandler::handle_whisper(const std::string &command, size_t *packet_len) {

    // Split into ['/whisper', 'username', 'message'] with maxsplit=2
    // Mirrors: parts = command.split(maxsplit=2)
    std::vector<std::string> parts;
    size_t pos = 0;
    int splits = 0;
    const int max_splits = 2;

    while (pos < command.size()) {
        // Skip whitespace
        while (pos < command.size() && command[pos] == ' ') pos++;
        if (pos >= command.size()) break;

        if (splits >= max_splits) {
            // Final token: rest of string is the message
            parts.push_back(command.substr(pos));
            break;
        }

        size_t end = command.find(' ', pos);
        if (end == std::string::npos) {
            parts.push_back(command.substr(pos));
            break;
        }

        parts.push_back(command.substr(pos, end - pos));
        pos = end + 1;
        splits++;
    }

    // Need at least: /whisper <username> <message>
    if (parts.size() < 3) {
        return build_packet("ERROR", "Usage: /whisper <username> <message>", packet_len);
    }

    const std::string &whisper_user = parts[1];
    const std::string &message      = parts[2];

    // Check if target user exists
    auto it = std::find(usernames->begin(), usernames->end(), whisper_user);
    if (it == usernames->end()) {
        std::string err = "User '" + whisper_user + "' not found";
        return build_packet("ERROR", err.c_str(), packet_len);
    }

    // Build whisper packet: body = "target_user|message"
    std::string body = whisper_user + "|" + message;
    return build_packet("WHISPER", body.c_str(), packet_len);
}
