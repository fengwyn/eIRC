`_________________________________________________________________`
`                       Internet Relay Channel                    `
`_________________________________________________________________`

( o > o)/

## Description

Internet Relay Channel is a system used to create, 
administrate and coordinate local and remote network nodes.

The Tracker server, instantiates a tracker ledger, used in the creation
and registration of nodes. Node servers have their own client tracker ledger,
and a node command module, used to implement commands during runtime.

It is also a message-passing system, allowing coordination between local and remote nodes.
A key purpose for this project is to allow outdated CPUs to be able to communicate
with modern containerized and coordinated applications, by simply allowing the containerized
application and the outdated machine to be able to communicate (message pass) between themselves,
and allow the containerized (modern) machine to behave as one.


## Goals
- Implement a master hub server (tracker) which allows clients to create and join servers.
- A node server allowing clients to pass messages, send files and allows for private messaging within the server.
- Allow node servers to handle non-socket related commands, which allows for live changes of the server's commands.
- A client interface which allows users to be able to interface with their OS' Shell as well as the Internet Relay Channel interface.



## Background and Strategic Fit

The server and client modules will utilize common utilities located at `/utils/`,
of which are: 
```
    * packet.c: Provides structured packets, `build_packet` and `unpack_packet`.

    * tracker.cpp: Provides a Parent Class `Tracker` and Inhereted Child Classes 
                    `ServerTracker` and `NodeTracker`, used by Tracker (master) server 
                    and Node (sub) Servers respectively.
    
    * interface.cpp: Provides functionalities for alternating between OS Shell and Internet Relay Channel interface. 
```



## User Interaction and Design

[PYTHON]
Run from project root directory, Internet Relay Channel/ then:
```
* Running Client (no Shell interface):      $ [WIP: python -m src.client.client <arguments>]
* Running Client (with Shell interface):    $ [WIP: python -m src.client.main <arguments>]

* Running Tracker Server: $ [WIP: python -m src.server.tracker <arguments>]
* Running Remote Server: $  [WIP: python -m src.server.server --hostname localhost --port 8888 --maxconns 32 --messagelength 64]
```

A `Tracker` server must be hosted by any system capable of creating socket connections.
A `Client` runs a provided `interface` which allows them to connect to a tracker server,
which then allows the user `Client` to use the Internet Relay Channel utilities.

A node server can be instantiated within `Tracker` by a `Client` by using the `/create` command
and following its use instructions, this will create a sub-server at the `Tracker`'s local address.
If a user want's to register their own remote server they'll utilize `/register` and follow the use instructions.

[C++]
make              # builds build/node
make packet-test  # builds standalone packet test binary
make packet-so    # builds packet.so for Python ctypes
make clean        # removes build/


## Directory Structure
```
    eIRC/               <- [WIP]
    |--src/                        
        ├── client/
        │   ├── __init__.py
        |   ├── client.py
        │   └── main.py
        ├── server/
        │   ├── node_commands.h
        │   ├── node_commands.c
        │   ├── server.h    <- Could provide common utilities for tracker and node (server/socket instantiations?)
        │   ├── tracker.h
        │   ├── tracker.cpp [WIP]
        │   ├── node.h
        │   └── node.cpp    [WIP]
        │   
        └── utils/
            ├── __init__.py
            ├─ packet.py     <- Used by Client
            ├─ packet.h      <- Used by Server (Tracker and Nodes)
            ├─ packet.c
            ├─ tracker.py    <- Will be replaced by C++ version
            ├─ tracker.h     <- Provides Class objects for data related methods, used by Tracker and Node
            ├─ tracker.cpp 
            ├─ interface.py
            ├─ logging.py
            ├─ crypto.py or crypto.cpp
            └─ others
```

## Notes && TODOs
DATABASES:
    Redis - Will be used as a high-speed buffer. The Nodes push sensor/message data here.
            It'll handle the "live" state (who is connected, current readings...).

    ClickHouse - It'll ingest batch data rows and allow us to run queries for building statistical models.

CHANGES:

    utils.tracker: Instead of providing a class for holding the server information via dict(), it'll use a Redis server

OpenMP / Parallelize:
Use OpenMP to parallelize packet processing, those threads can all fire PUBLISH commands to a single Redis instance.

`_________________________________________________________________`
42 79 20 66 65 6E 67 77 79 6E 28 20 6F 20 3E 20 6F 29