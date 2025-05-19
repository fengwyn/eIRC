                                *eIRC*

## Description

An internet relay channel/chat capable of registering local and remote servers
Provides a tracker (master) server which allows clients to create and join chat servers
The tracker and chat servers utilize a tracker module for seamless service integration



## Background and Strategic Fit

The server and client modules will utilize common utilities located at `/utils/`,
of which are: 
```
    * packet.py: Provides structured packets, `build_packet` and `unpack_packet`.

    * tracker.py: Provides a Parent Class `Tracker` and Inhereted Child Classes 
                    `ServerTracker` and `ChatTracker`, used by Tracker (master) server 
                    and Chat (sub) Servers respectively.
    
    * interface.py: Provides functionalities for alternating between OS Shell and eIRC interface. 
```



## User Interaction and Design

Run from project root directory, eIRC/ then:
```
* Running Client (no Shell interface):      $ python -m src.client.client <arguments>
* Running Client (with Shell interface):    $ python -m src.client.main <arguments>

* Running Tracker Server: $ python -m src.server.tracker <arguments>
* Running Remote Server: $ python -m src.server.server --hostname localhost --port 8888 --maxconns 32 --messagelength 64
```

A `Tracker` server must be hosted by any system capable of creating socket connections.
A `Client` runs a provided `interface` which allows them to connect to a tracker server,
which then allows the user `Client` to use the eIRC utilities.

A chat server can be instantiated within `Tracker` by a `Client` by using the `/create` command
and following its use instructions, this will create a sub-server at the `Tracker`'s local address.
If a user want's to register their own remote server they'll utilize `/register` and follow the use instructions.



## Directory Structure
```
    eIRC/               <- Run application from here
    |--src/                        
        ├── client/
        │   ├── __init__.py
        │   └── client.py
        ├── server/
        │   ├── __init__.py
        │   └── server.py
        └── utils/
            ├── __init__.py
            └── packet.py
```



## Goals
- Implement a master hub server (tracker) which allows clients to create and join servers.
- A chat server allowing clients to chat, send files and allows for private messaging within the server.
- Allow chat servers to handle non-socket related commands, which allows for live changes of the server's commands.
- A client interface which allows users to be able to interface with their OS' Shell as well as the eIRC interface.


