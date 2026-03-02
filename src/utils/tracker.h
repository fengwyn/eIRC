#ifndef TRACKER_H
#define TRACKER_H

// tracker.h: C++ equivalent of utils/tracker.py
// Provides Tracker (parent), ServerTracker and NodeTracker (children)
// Thread-safe via mutex — all shared-state operations lock before writing

#include <string>
#include <unordered_map>
#include <mutex>


// Parent class: manages admins and members behind a mutex
// Used by both the master hub (ServerTracker) and node rooms (NodeTracker)
class Tracker {

protected:

    std::string name;
    std::string address;
    bool is_private;
    std::string passkey;

    std::mutex lock;

    // admins:  username -> address
    std::unordered_map<std::string, std::string> admins;
    // members: username/servername -> address
    std::unordered_map<std::string, std::string> members;


public:

    Tracker(const std::string &name, const std::string &address,
            const std::string &creator_user, const std::string &creator_address,
            bool is_private, const std::string &passkey);

    virtual ~Tracker() = default;


    // --- Admin operations ---

    void add_admin(const std::string &user, const std::string &addr);
    void remove_admin(const std::string &user);
    std::unordered_map<std::string, std::string> list_admins();


    // --- Member operations ---

    void add_member(const std::string &member, const std::string &addr);
    void remove_member(const std::string &member);
    std::unordered_map<std::string, std::string> list_members();


    // --- Accessors ---

    void set_name(const std::string &new_name);
    void set_address(const std::string &new_address);
    std::string get_name() const;
    std::string get_address() const;
};



// ServerTracker: directory of registered node servers (used by TrackerDaemon)
class ServerTracker : public Tracker {

public:

    struct ServerMeta {
        bool is_private;
        std::string passkey;
        std::string admin_user;
        std::string admin_address;
    };

private:

    std::unordered_map<std::string, ServerMeta> server_metadata;

public:

    ServerTracker(const std::string &name, const std::string &address,
                  const std::string &creator_user, const std::string &creator_address,
                  bool is_private, const std::string &passkey);

    void register_server(const std::string &server_name, const std::string &server_address,
                         const std::string &admin_user, const std::string &admin_address,
                         bool is_private, const std::string &passkey);

    std::unordered_map<std::string, std::string> get_server_list();

    // Returns nullptr if server not found
    const ServerMeta* get_server_info(const std::string &server_name);
};



// NodeTracker: tracks active users on a single node room (used by Node server)
class NodeTracker : public Tracker {

public:

    NodeTracker(const std::string &name, const std::string &address,
                const std::string &creator_user, const std::string &creator_address,
                bool is_private, const std::string &passkey);

    void user_join(const std::string &user, const std::string &user_address);
    void user_leave(const std::string &user);
    std::unordered_map<std::string, std::string> get_active_users_list();
    std::unordered_map<std::string, std::string> get_admin_list();
};


#endif // TRACKER_H
