from __future__ import annotations
from enum import Enum

import log
import telnet

class Router:
    def __init__(self, name: str, asn: int, a_s: AS, host, port, id: str = ""):
        self.name: str = name
        self.asn: int = asn
        self.a_s: AS = a_s
        self.host: str = host
        self.port: str = port

        self.interfaces: dict[str, list[str]] = {
            "Loopback0":[],
            "g1/0": [],
            "g2/0": [],
            "g3/0": [],
            "g4/0": []
        }

        if id == "":
            self.id: str = self.name[1:]
        else:
            self.id: str = id

        self.cmds: list[str] = []
        self.a_s: AS 

    def append_cmd(self, cmd: str): # Single command
        self.cmds.append(cmd)
    
    def append_cmds(self, cmds: list[str]): # List of commands
        self.cmds += cmds

    def send_cmds(self):
        self.append_cmd("end")

        telnet.run_on_router(self.cmds, self.host, self.port)

        log.success(f"Finished config of [b]{self.name}[/]")



class Interface:
    def __init__(self):
        pass

class AS:
    def __init__(self, asn: int, internal_protocol: str):
        self.asn: int = asn
        self.internal_protocol: str = internal_protocol
        
        self.routers: dict[str, Router] = {}