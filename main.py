import json
import gns
import commands
from ip_utils import *

INTENT_PATH = "intent_projet.json"

def find_as(intent, name):
    for router in intent["routers"]:
        if router["name"] == name:
            return router["as"]


def find_internal_protocol(intent, as_nb):
    for as_ in intent["as"]:
        if str(as_["nb"]) == str(as_nb):
            return as_["internal_protocol"]


def cmd_configure_interface(intent, name, interface, to, link_type):
        cmd_list = []
        as_nb = find_as(intent, name)
        addr = ipv6_link_intra_as(name, to, as_nb)[name]

        print(f"Configuring {interface} on {name}")

        cmd_list += commands.address_config(interface, addr) # Up the interface and setting ip address
        
        if link_type == "intra-as":
            if find_internal_protocol(intent, as_nb) == "RIP":
                print(f"Enabling RIP")
                cmd_list += commands.rip_config(addr, interface, name)

            elif find_internal_protocol(intent, as_nb) == "OPSF":
                print(f"Enabling OSPF")
                cmd_list += commands.opsf_config(addr, interface, name, 0)

        if link_type == "inter-as":
            # Implement BGP
            pass

        return cmd_list


if __name__ == "__main__":
    cmds = {}

    ### Reading the intent file
    f = open(INTENT_PATH, "r", encoding="utf-8")
    intent = json.load(f)
    f.close()


    ### Project opening
    print("Opening the project...")
    g = gns.GnsProject(name=intent["project_name"])
    g.create_new(auto_recover=True)
    g.open()
    print("Opened the project")


    ### Router setup
    for router in intent["routers"]:
        name = router["name"]

        print(f"Creating router {name}")
        g.create_router(name=name, auto_recover=True)

        print("Configuring the router")
        cmds[name] = commands.base_router_config(name)
        

    ### Link and protocol setup
    for link in intent["links"]:
        print(f"Adding link from {link["interface_from"]} on {link["from"]} to {link["interface_to"]} on {link["to"]}")
        g.create_link(link["from"], # Adding link inside GNS
                    link["interface_from"],
                    link["to"],
                    link["interface_to"])


        # Configure the interface for both routers of the link
        cmds[name] += cmd_configure_interface(intent,
                                                  link["from"],
                                                  link["interface_from"],
                                                  link["to"],
                                                  link["type"])

        cmds[name] += cmd_configure_interface(intent,
                                                  link["to"],
                                                  link["interface_to"],
                                                  link["from"],
                                                  link["type"])

    for name, cmd in cmds.items():
        print(f"Running config for {name}")
        print(cmd)
        g.routers[name].start()
        g.run_on_router(name, cmd)

    g.lab.arrange_nodes_circular()