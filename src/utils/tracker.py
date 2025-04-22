# Tracker Object for Handling Hosts, User logs and Redirect Connections
# from common import SharedQueue    # <--- Useful if buffering is required
import logging
import threading

# Will be accessed asynchronically, must protect with mutex
# There are two ways to utilize the tracker, for redirect servers and for chat servers
# Redirect Servers keep track of active servers, Chat servers keep track of active users

class Tracker(Thread):

    # Requires server info, admin (creator) info, 
    # if isprivate True, requires passkey

    def __init__(self, servername, serveraddress, \
                creatoruser, creatoraddress, \
                isprivate, passkey):
        
        self.servername = servername
        self.serveraddress = serveraddress

        self.creatoruser = creatoruser
        self.creatoraddress = creatoraddress

        self.isprivate = isprivate
        self.passkey = passkey

        # Using a hashmap / dict() for saving username: str and ipaddr: addr
        self.adminlist = dict()
        # Creator is an admin
        adminlist[creatoruser] = creatoraddress

        # If Tracker Server; userlist consists of registered chat servers
        # If Chat Server; userlist consists of users in those servers
        self.userlist = dict()
    
    # Puts / Setters
    
    # Utilized when updating server name
    def putservername(self, servername):
        self.servername = servername

    # Utilized when updating server address
    def putserveraddress(self):
        self.serveraddress = serveraddress

    # Puts user's name and IP into userlist
    def putuserintoserver(self, user, addr):
        self.userlist[user] = addr

    # Getters
    def getservername(self):
        return self.servername 

    def getserveraddress(self):        
        return self.serveraddress

    # Returns hashmap / dict() object
    def getuserlist(self):
        return self.userlist


class TrackerServer(Tracker):

    def __init__(self, trackername, trackeraddress, \
                creatoruser, creatoraddress, \
                isprivate, passkey):

        trackerserver = Tracker(servername=trackername, serveraddress=trackeraddress, \
                        creatoruser=creatoruser, creatoraddress=creatoraddress, \
                        isprivate=isprivate, passkey=passkey)


        def putserver(servername, serveraddress, creatoruser, creatoraddress, isprivate, passkey):
            # TODO: This doesn't guarantees that the creator will be the admin by default ---- Perhaps change approach of 
            # adding servers into the Tracker servers? 
            trackerserver.putuserintoserver(servername, serveraddress)
            
            pass

        def getserverlist():
            pass


class ChatServer(Tracker):

    def __init__(self, servername, serveraddress, \
                creatoruser, creatoraddress, \
                isprivate, passkey):
        
        chatserver = Tracker(servername=servername, serveraddress=serveraddress, \
                    creatoruser=creatoruser, creatoraddress=creatoraddress, \
                    isprivate=isprivate, passkey=passkey)
