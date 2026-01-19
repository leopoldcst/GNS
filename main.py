import json
import multiprocessing
import typing

import click

import gns
import commands
from ip_utils import *
import log
from log import console
from utils import *


### CLI Arguments
@click.command()
# @click.option('--count', default=1, help='Number of greetings.')
@click.argument('intentfile', type=click.Path(exists=True, readable=True), default="./intent_projet.json")
def main(intentfile):
    console.print("[b][blue]GNS configuring util[/b][/blue]")
    console.print(f"Intent file is [b]{intentfile}[/b]")

    cmds = {}

    ### Reading the intent file
    intents = read_intents(intentfile)

    ### Check if we use gnsfy
    use_gnsfy = False    
    gns_config: dict[str, typing.Any] = intents.get("gns_auto_config")

    if gns_config and gns_config.get("enable"):
        use_gnsfy = True


    ### Project opening
    if use_gnsfy:
        g = open_gns(gns_config)

    ##### Creating data structures
    ### ASs
    as_list: dict[int, AS] = {}
    for as_data in intents["as"]:
        asn = as_data["asn"]
        internal_protocol = as_data["internal_protocol"].lower()

        as_list[asn] = AS(asn, internal_protocol)

    ### Routers
    routers: dict[str, Router] = {}

    for router_data in intents["routers"]:
        name: str = router_data["name"]
        asn: int = router_data["asn"]
        
        # Getting host and port depending on choosed method,
        # either automaticaly from GNS or with the user's intents
        port = router_data.get("port")
        host = router_data.get("host")

        if use_gnsfy and gns_config["create_routers"]:
            try:
                log.info(f"Creating/recovering router {name} (GNS)")
                g.create_router(name=name, auto_recover=True) # Creating/recovering router in GNS
            except Exception as exp:
                log.fatal_error("Failed to create/recover the router {name} (GNS)", exp)

            if gns_config["auto_fetch_router_infos"]:
                port = g.get_router_port(name)
                host = gns_config.get("ip", "127.0.0.1")

        if host is None or port is None:
            if gns_config["auto_fetch_router_infos"]:
                log.fatal_error(f"Failed to fetch the host or port for {name}", Exception("Can't fetch host/port on GNS"))
            else:
                log.fatal_error(f"Failed to fetch the host or port for {name}", Exception("Can't get host/port in intent"))

        routers[name] = Router(name, asn, as_list[asn], host, port)
        as_list[asn].routers[name] = routers[name]

        # Basic router config
        routers[name].append_cmds(commands.base_router_config(name))
        

    ### Link and protocol setup
    for link in intents["links"]:
        router_a: Router = routers[link["from"]]
        router_b: Router = routers[link["to"]]
        interface_a: str = link["interface_from"]
        interface_b: str = link["interface_to"]


        if gns_config["create_links"]:
            log.info(f"Adding link from {link["interface_from"]} on {link["from"]} to {link["interface_to"]} on {link["to"]} (GNS)")
            g.create_link(link["from"], # Adding link inside GNS
                        link["interface_from"],
                        link["to"],
                        link["interface_to"])

        #### !!!!! link["type"] est redondant car on peut le déduire à partir de l'as de chaque routeur
        # Configure the interface for both routers of the link
        configure_interfaces(router_a, router_b, interface_a, interface_b, link["type"])


    ### Enable BGP on every router
    for name, r in routers.items():
        r.append_cmds(commands.bgp_config(r.id, r.asn))


    ##### iBGP config
    for asn, a_s in as_list.items():
        # We first need to enable the loopback interface on all the routers before configuring iBGP
        for name, r in a_s.routers.items():
            loopback_addr = compute_loopback_address(name, asn)

            ### Adding loopback address
            r.interfaces["Loopback0"].append(loopback_addr)
            r.append_cmds(commands.loopback_config(
                loopback_addr,
                a_s.internal_protocol,
                r.id))

        for name, r in a_s.routers.items():
            ### Full mesh iBGP sessions
            r.append_cmds(commands.enter_bgp_config(asn))

            for name_other, r_other in a_s.routers.items():
                if name_other == name:
                    continue

                other_ip_without_mask = remove_ipv6_mask(r_other.interfaces["Loopback0"][0])

                r.append_cmds(commands.i_bgp_neighbor(other_ip_without_mask, asn, "Loopback0"))

            r.append_cmd("exit")


    ### Start all router on GNS
    if use_gnsfy:
        with console.status("[blue] Starting routers (GNS)...") as status:
            for name in routers.keys():
                g.routers[name].start()

        log.success("Started routers (GNS)")


    ### Telnet sending
    processes = []

    with console.status("[blue] Sending commands to routers") as status:
        for r in routers.values():
            log.info(f"Starting Telnet to [b]{r.name}[/] on {r.host}://{r.port}")
        
            processes.append(multiprocessing.Process(target=r.send_cmds))
            processes[-1].start()

        for i in range(len(processes)):
            processes[i].join()


    if use_gnsfy and gns_config["arrange_in_circle"]:
        g.lab.arrange_nodes_circular()
    
    console.print("\n[b][green]Finished![/b][/green]")


def configure_interfaces(r_a: Router, r_b: Router, interface_a: str, interface_b: str, link_type: str):
    log.info(f"Configuring {interface_a} on {r_a.name}")
    log.info(f"Configuring {interface_b} on {r_b.name}")

    addr_a, addr_b = compute_ip_address(r_a, r_b)

    r_a.append_cmds(commands.address_config(interface_a, addr_a))
    r_b.append_cmds(commands.address_config(interface_b, addr_b))

    r_a.interfaces[interface_a].append(addr_a)
    r_b.interfaces[interface_b].append(addr_b)
    
    # Internal protocol setup
    if r_a.asn == r_b.asn: # Same as
    # if link_type == "intra-as":
        protocol = r_a.a_s.internal_protocol

        if protocol == "rip":
            log.info(f"Enabling RIP")
            r_a.append_cmds(commands.rip_config(addr_a, interface_a, r_a.name))
            r_b.append_cmds(commands.rip_config(addr_b, interface_b, r_b.name))

        elif protocol == "ospf":
            log.info(f"Enabling OSPF")
            r_a.append_cmds(commands.ospf_config(addr_a, interface_a, r_a.name, 0))
            r_b.append_cmds(commands.ospf_config(addr_b, interface_b, r_b.name, 0))

    # Inter as protocol AKA eBGP
    else: # Different as
    # if link_type == "inter-as":
        log.info(f"Enabling eBGP")

        addr_a_without_mask = remove_ipv6_mask(addr_a)
        addr_b_without_mask = remove_ipv6_mask(addr_b)

        r_a.append_cmds(commands.e_bgp_neighbor_config(r_a.asn, addr_b_without_mask, r_b.asn))
        r_b.append_cmds(commands.e_bgp_neighbor_config(r_b.asn, addr_a_without_mask, r_a.asn))


def read_intents(path) -> dict[str, typing.Any] :
    try:
        log.info("Reading the intent file...")

        f = open(path, "r", encoding="utf-8")
        intents = json.load(f)
        f.close()
        
        log.success("Read the intents")
    except Exception as exp:
        log.fatal_error("Failed to read the intent file", exp)
        
    return intents


def open_gns(gns_config):
    log.info("Auto config is enabled, connecting to the server... (GNS)")

    try:
        g = gns.GnsProject(name=gns_config["project_name"], ip=gns_config.get("ip", "http://localhost"), port=gns_config.get("port", 3000))
        g.create_new(auto_recover=True)
        g.open()
    
        log.success("Opened/created the project (GNS)")

    except Exception as exp:
        log.fatal_error("Failed to connect to the GNS server", exp)

    return g


if __name__ == "__main__":
    main()