def base_router_config(name):
    return [
        "enable",
        "configure terminal",
        f"hostname {name}",
        "ipv6 unicast-routing",
        "end",
        " "
    ]


def address_config(interface, address):
    return [
        "enable",
        "configure terminal",
        f"interface {interface}",
        "ipv6 enable",
        f"ipv6 address {address}",
        "no shutdown",
        "exit",
        "end",
        " " # on force le end à se faire
    
    ]


def rip_config(address, interface, name):
    process_name = "RIP_AS"
    conf = []
    # conf += baseRouterConfig(name)
    # conf += addressConfig(interface,address)
    conf += [
        "enable"
        "configure terminal"
        f"interface {interface}",
        f"ipv6 router rip {process_name}",
        "exit",
        f"interface {interface}",
        f"ipv6 rip {process_name} enable",
        "end",
        " "
    ]

    return conf


def ospf_config(address, interface, name, area_nb):
    conf = []
    process_id = int(name[1:])
    # conf += baseRouterConfig(name)
    # conf += addressConfig(interface,address)
    conf += [
        "enable",
        "configure terminal",
        f"ipv6 router ospf {process_id}",
        f"router-id {process_id}.{process_id}.{process_id}.{process_id}",
        f"interface {interface}"
        f"ipv6 ospf {process_id} area {area_nb}",
        "end",
        " "
    ]

    return conf

   #"redistribute connected" à activer si on veut partager tous les sous reseaux auxquels on appartient, ce qui n'est pas le cas tout le temps :)