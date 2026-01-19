import json
import multiprocessing

import click
from rich.console import Console
console = Console()
import ipaddress


import gns
import commands
from ip_utils import *

INTENT_PATH = "intent_projet.json"

### CLI Arguments
@click.command()
# @click.option('--count', default=1, help='Number of greetings.')
@click.argument('intentfile', type=click.Path(exists=True, readable=True), default="./intent_projet.json")
def main(intentfile):
    console.print("[b][blue]GNS configuring util[/b][/blue]")
    console.print(f"Configuring [b]GNS[/b] from {intentfile}")

    cmds = {}

    adress = {}

    ### Reading the intent file
    f = open(INTENT_PATH, "r", encoding="utf-8")
    intent = json.load(f)
    f.close()




    ### Project opening
    console.log("Opening the project...")
    g = gns.GnsProject(name=intent["project_name"])
    g.create_new(auto_recover=True)
    g.open()
    console.log("Opened the project")

## construction of a border router dictionnary

    border_routers = set()
    for link in intent["links"]:
        if link["type"] == "inter-as":
            border_routers.add(link["from"])
            border_routers.add(link["to"])



    ### Router setup
    if intent["createRouters"]:
        for router in intent["routers"]:
            name = router["name"]

            print(f"Creating router {name}")
            if find_as(intent, name) == 1:
                g.create_router(name=name, auto_recover=True, x=0, y=0)
            elif find_as(intent, name) == 2:
                g.create_router(name=name, auto_recover=True, x=100, y=0)
            else:
                g.create_router(name=name, auto_recover=True, x=200, y=0)


            print("Configuring the router")
            cmds[name] = commands.base_router_config(name)
        

    ### Link and protocol setup
    for link in intent["links"]:
        if intent["createLinks"]:
            print(f"Adding link from {link["interface_from"]} on {link["from"]} to {link["interface_to"]} on {link["to"]}")
            g.create_link(link["from"], # Adding link inside GNS
                        link["interface_from"],
                        link["to"],
                        link["interface_to"])


        # Configure the interface for both routers of the link
        cmds[link["from"]] += cmd_configure_interface(intent,
                                                    link["from"],
                                                    link["interface_from"],
                                                    link["to"],
                                                    link["type"],
                                                    adress)

        cmds[link["to"]] += cmd_configure_interface(intent,
                                                    link["to"],
                                                    link["interface_to"],
                                                    link["from"],
                                                    link["type"],
                                                    adress)



    ### Enable BGP on every router
    for router in intent["routers"]:
        cmds[router["name"]] += commands.bgp_config(router["name"][1:], router["as"])

    ### iBGP config

    # Find routers of the same as
    # Construct a dictionnary with the router in the AS and their respective loopback address
    for as_ in intent["as"]:
        as_nb = as_["nb"]
        as_routers = []

        for router in intent["routers"]:
            if str(router["as"]) != str(as_nb):
                continue

            ### Adding loopback address
            ipv6_loopback_adress = ipv6_loopback(router["name"], as_nb)
            cmds[router["name"]] += commands.loopback_config(ipv6_loopback_adress,
                                                             as_["internal_protocol"],
                                                             router["name"][1:])
            
            adress.setdefault(router["name"], {})
            adress[router["name"]]["Loopback0"] = ipv6_loopback_adress
            


            as_routers.append({
                "name": router["name"],
                "loopback": ipv6_loopback(router["name"], router["as"])
            })

        # print(as_routers)
        # print(commands.whole_as_i_bgp_config(as_routers, as_nb))

        for name, cmd in commands.whole_as_i_bgp_config(as_routers, as_nb).items():
            cmds[name] += cmd

# border routers only
        for router in as_routers:
            name = router["name"]
            if name not in border_routers:
                continue

            neighbors = [
                r["loopback"].split("/")[0]
                for r in as_routers
                if r["name"] != name
            ]
            cmds[name] += commands.next_hop_self(as_nb, neighbors)

            protocol = as_["internal_protocol"]

            if protocol.upper() == "OSPF":
                process_id = int(name[1:])

            else:
                process_id = "RIP_AS"  # ou None si ta fonction a un defaut

            cmds[name] += commands.redistribute_iBGP(as_nb, protocol, process_id)




    write_configs(cmds, g)

    if intent["arrangeInCircle"]:
        g.lab.arrange_nodes_circular()

    ##console.print(adress)
    
    console.print("[b][blue]Finished![/b][/blue]")


def find_as(intent, name):
    for router in intent["routers"]:
        if router["name"] == name:
            return router["as"]


def find_internal_protocol(intent, as_nb):
    for as_ in intent["as"]:
        if str(as_["nb"]) == str(as_nb):
            return as_["internal_protocol"]


def cmd_configure_interface(intent, name, interface, to, link_type, adress):
    cmd_list = []
    as_nb = find_as(intent, name)

    adress.setdefault(name, {})

    print(f"Configuring {interface} on {name}")

    
    if link_type == "intra-as":
        addr = ipv6_link_intra_as(name, to, as_nb)[name]
        adress[name][interface] = addr
        cmd_list += commands.address_config(interface, addr) # Up the interface and setting ip address
        # cmd_list += commands.address_config("Loopback0", ipv6_loopback(name, as_nb))

        protocol = find_internal_protocol(intent, as_nb)

        if protocol == "RIP":
            print(f"Enabling RIP")
            cmd_list += commands.rip_config(addr, interface, name)
            # cmd_list += commands.loopback_config(ipv6_loopback(name, as_nb), "RIP", "RIP_AS")

        elif protocol == "OSPF":
            print(f"Enabling OSPF")
            cmd_list += commands.ospf_config(addr, interface, name, 0)


    if link_type == "inter-as":
        # Implement BGP
        print(f"Enabling eBGP")
        to_as_nb = find_as(intent, to)
        to_addr = commands.ipv6_sans_masque(ipv6_link_inter_as(name, as_nb, to, to_as_nb)[to])
    
        addr = ipv6_link_inter_as(name, as_nb, to, to_as_nb)[name]
        adress[name][interface] = addr

        cmd_list += commands.address_config(interface, addr) # Up the interface and setting ip address

        prefix = str(ipaddress.IPv6Interface(addr).network)
        cmd_list += commands.bgp_advertise_network(as_nb, prefix)

        cmd_list += commands.e_bgp_neighbor_config(as_nb, to_addr, to_as_nb)
    

    return cmd_list


def write_configs(cmds, g):
    processes = []


    with console.status("[bold green] Sending commands to routers") as status:
        for name, cmd in cmds.items():
            # print(f"Running config for {name}")
            console.log(f"Sending to {name}")

            processes.append(multiprocessing.Process(target=write_config_router, args=(name, cmd, g)))
            
            processes[-1].start()

        for i in range(len(cmds)):
            processes[i].join()
            # for c in cmd:
            #     print(c)

    

def write_config_router(name, cmd, g):
    cmd.append("end")
    g.routers[name].start()
    g.run_on_router(name, cmd)

    console.log(f"Finished config of [b][green]{name}[/b][/green]")


if __name__ == "__main__":
    main()