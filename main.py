import json
import multiprocessing

import click
from rich.console import Console
console = Console()
import ipaddress
import time


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
            g.create_router(name=name, auto_recover=True)

            print("Configuring the router")
            cmds[name] = commands.base_router_config(name)
            cmds[name] += commands.enable_community()
        

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

            ## tag des routes
            for rel in intent.get("clientProviderRelationships", []):
                cmds[name] += tag_community(intent, as_nb, name, border_routers, adress, rel, "client", "provider", "provider", "TAG_PROVIDER", "PROVIDER")
                cmds[name] += tag_community(intent, as_nb, name, border_routers, adress, rel, "provider", "client", "client", "TAG_CLIENT", "CLIENT")

            for rel in intent.get("peerTopeer", []):
                cmds[name] += tag_community(intent, as_nb, name, border_routers, adress, rel, "peer1", "peer2", "peer", "TAG_PEER", "PEER")
                cmds[name] += tag_community(intent, as_nb, name, border_routers, adress, rel, "peer2", "peer1", "peer", "TAG_PEER", "PEER")
            
            ## appliquer les conditions en fonction de la relation entre les AS
            cmds[name] += apply_community_conditions(intent, as_nb, name, adress)







                    


        







    write_configs(cmds, g)

    if intent["arrangeInCircle"]:
        g.lab.arrange_nodes_circular()

    ##console.print(cmds['R8'])
    
    console.print("[b][blue]Finished![/b][/blue]")


def find_as(intent, name):
    for router in intent["routers"]:
        if router["name"] == name:
            return router["as"]


def find_internal_protocol(intent, as_nb):
    for as_ in intent["as"]:
        if str(as_["nb"]) == str(as_nb):
            return as_["internal_protocol"]


def tag_community(intent, as_nb, name, border_routers, adress, rel, local_key, remote_key, community_key, route_map_tag, community_list_name):
    if str(rel[local_key]) != str(as_nb):
        return []

    value_community = f"{as_nb}:{intent['valueCommunity'][community_key]}"
    cmd_list = []
    cmd_list += commands.create_route_map(route_map_tag, community=value_community)

    remote_as = rel[remote_key]

    for routeur in border_routers:
        routeur_as = find_as(intent, routeur)
        if str(routeur_as) != str(as_nb) and str(routeur_as) == str(remote_as):
            for liens in intent["links"]:
                if liens["from"] == name and liens["to"] == routeur:
                    neighbor_addr = commands.ipv6_sans_masque(
                        adress[routeur][liens["interface_to"]]
                    )
                    cmd_list += commands.apply_route_map(
                        neighbor_addr, route_map_tag, as_nb
                    )

                elif liens["from"] == routeur and liens["to"] == name:
                    neighbor_addr = commands.ipv6_sans_masque(
                        adress[routeur][liens["interface_from"]]
                    )
                    cmd_list += commands.apply_route_map(
                        neighbor_addr, route_map_tag, as_nb
                    )

    cmd_list += commands.create_community_list(community_list_name, value_community)
    return cmd_list


def get_relation_type(intent, as_nb, neighbor_as):
    for rel in intent.get("clientProviderRelationships", []):
        if str(rel["client"]) == str(as_nb) and str(rel["provider"]) == str(neighbor_as):
            return "provider"
        if str(rel["provider"]) == str(as_nb) and str(rel["client"]) == str(neighbor_as):
            return "client"

    for rel in intent.get("peerTopeer", []):
        if (str(rel["peer1"]) == str(as_nb) and str(rel["peer2"]) == str(neighbor_as)) or (
            str(rel["peer2"]) == str(as_nb) and str(rel["peer1"]) == str(neighbor_as)
        ):
            return "peer"

    return None


def apply_community_conditions(intent, as_nb, name, adress):
    cmd_list = []
    block_lists = []

    for rel in intent.get("clientProviderRelationships", []):
        if str(rel["client"]) == str(as_nb) and "PROVIDER" not in block_lists:
            block_lists.append("PROVIDER")

    for rel in intent.get("peerTopeer", []):
        if (str(rel["peer1"]) == str(as_nb) or str(rel["peer2"]) == str(as_nb)) and "PEER" not in block_lists:
            block_lists.append("PEER")

    if block_lists:
        cmd_list += commands.create_route_map(
            "BLOCK_UPSTREAM",
            deny=True,
            community_list=" ".join(block_lists),
        )

    for link in intent["links"]:
        if link["type"] != "inter-as":
            continue
        if link["from"] == name:
            neighbor = link["to"]
            neighbor_iface = link["interface_to"]
        elif link["to"] == name:
            neighbor = link["from"]
            neighbor_iface = link["interface_from"]
        else:
            continue

        neighbor_as = find_as(intent, neighbor)
        relation = get_relation_type(intent, as_nb, neighbor_as)

        if relation in ("provider", "peer") and block_lists:
            neighbor_addr = commands.ipv6_sans_masque(adress[neighbor][neighbor_iface])
            cmd_list += commands.apply_route_map(neighbor_addr, "BLOCK_UPSTREAM", as_nb, entry=False)

    return cmd_list


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

        cmd_list += commands.send_community(as_nb, to_addr)

    

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

    time.sleep(10)

    g.run_on_router(name, cmd)

    console.log(f"Finished config of [b][green]{name}[/b][/green]")


if __name__ == "__main__":
    main()
