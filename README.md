[How to Run]

Run from project root directory, eIRC/ then:
```
* Client: $ python -m src.client.client <arguments>

* Server: $ python -m src.server.server --hostname localhost --port 8888 --maxconns 32 --messagelength 64
```

This is so that we can utilize build_packet which is located in src/utils

```
[Directory Structure]
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