// tracker.cpp: C++ equivalent of utils/tracker.py
// Implements Tracker (parent), ServerTracker and NodeTracker (children)
//
// All shared-state writes are protected by std::mutex.
// Getters that return copies also lock to prevent torn reads.

#include "tracker.h"

#include <cstdio>
#include <mutex>
#include <string>
#include <unordered_map>


// ===========================================================================
//  Tracker (parent class)
// ===========================================================================

Tracker::Tracker(const std::string &name, const std::string &address,
                 const std::string &creator_user, const std::string &creator_address,
                 bool is_private, const std::string &passkey)
    : name(name)
    , address(address)
    , is_private(is_private)
    , passkey(passkey)
{
    // Add the creator as default admin (mirrors tracker.py __init__)
    add_admin(creator_user, creator_address);
}


// --- Admin operations ---

void Tracker::add_admin(const std::string &user, const std::string &addr) {

    std::lock_guard<std::mutex> guard(lock);
    admins[user] = addr;
    fprintf(stderr, "[tracker] Added admin %s@%s to tracker '%s'\n",
            user.c_str(), addr.c_str(), name.c_str());
}


void Tracker::remove_admin(const std::string &user) {

    std::lock_guard<std::mutex> guard(lock);
    auto it = admins.find(user);
    if (it != admins.end()) {
        admins.erase(it);
        fprintf(stderr, "[tracker] Removed admin %s from tracker '%s'\n",
                user.c_str(), name.c_str());
    }
}


std::unordered_map<std::string, std::string> Tracker::list_admins() {

    std::lock_guard<std::mutex> guard(lock);
    return admins;  // returns a copy
}


// --- Member operations ---

void Tracker::add_member(const std::string &member, const std::string &addr) {

    std::lock_guard<std::mutex> guard(lock);
    members[member] = addr;
    fprintf(stderr, "[tracker] Added member %s@%s to tracker '%s'\n",
            member.c_str(), addr.c_str(), name.c_str());
}


void Tracker::remove_member(const std::string &member) {

    std::lock_guard<std::mutex> guard(lock);
    auto it = members.find(member);
    if (it != members.end()) {
        members.erase(it);
        fprintf(stderr, "[tracker] Removed member %s from tracker '%s'\n",
                member.c_str(), name.c_str());
    }
}


std::unordered_map<std::string, std::string> Tracker::list_members() {

    std::lock_guard<std::mutex> guard(lock);
    return members;  // returns a copy
}


// --- Accessors ---

void Tracker::set_name(const std::string &new_name) {

    // NOTE: tracker.py uses self.lock.locked() here which is a bug
    // (returns bool, doesn't acquire). We do it correctly.
    std::lock_guard<std::mutex> guard(lock);
    name = new_name;
}


void Tracker::set_address(const std::string &new_address) {

    std::lock_guard<std::mutex> guard(lock);
    address = new_address;
}


std::string Tracker::get_name() const {
    // Matches Python: no lock on read (name is set once at construction, rarely changed)
    return name;
}


std::string Tracker::get_address() const {
    return address;
}



// ===========================================================================
//  ServerTracker — directory of registered node servers
// ===========================================================================

ServerTracker::ServerTracker(const std::string &name, const std::string &address,
                             const std::string &creator_user, const std::string &creator_address,
                             bool is_private, const std::string &passkey)
    : Tracker(name, address, creator_user, creator_address, is_private, passkey)
{
}


void ServerTracker::register_server(const std::string &server_name, const std::string &server_address,
                                    const std::string &admin_user, const std::string &admin_address,
                                    bool is_private, const std::string &passkey) {

    // Register via parent's add_member (server_name -> server_address)
    add_member(server_name, server_address);

    // Store server metadata under lock
    {
        std::lock_guard<std::mutex> guard(lock);
        server_metadata[server_name] = {is_private, passkey, admin_user, admin_address};
    }

    fprintf(stderr, "[tracker] Registered node server %s@%s\n",
            server_name.c_str(), server_address.c_str());
}


std::unordered_map<std::string, std::string> ServerTracker::get_server_list() {

    return list_members();
}


const ServerTracker::ServerMeta* ServerTracker::get_server_info(const std::string &server_name) {

    std::lock_guard<std::mutex> guard(lock);
    auto it = server_metadata.find(server_name);
    if (it != server_metadata.end()) {
        return &it->second;
    }
    return nullptr;
}



// ===========================================================================
//  NodeTracker — tracks active users on a single node room
// ===========================================================================

NodeTracker::NodeTracker(const std::string &name, const std::string &address,
                         const std::string &creator_user, const std::string &creator_address,
                         bool is_private, const std::string &passkey)
    : Tracker(name, address, creator_user, creator_address, is_private, passkey)
{
}


void NodeTracker::user_join(const std::string &user, const std::string &user_address) {
    add_member(user, user_address);
}


void NodeTracker::user_leave(const std::string &user) {
    remove_member(user);
}


std::unordered_map<std::string, std::string> NodeTracker::get_active_users_list() {
    return list_members();
}


std::unordered_map<std::string, std::string> NodeTracker::get_admin_list() {
    return list_admins();
}
