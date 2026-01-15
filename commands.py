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
        f" router-id {process_id}.{process_id}.{process_id}.{process_id}",
        "exit",
        f"interface {interface}",
        f" ipv6 ospf {process_id} area {area_nb}",
        "exit",
        "end",
        " "
    ]

    return conf


   #"redistribute connected" à activer si on veut partager tous les sous reseaux auxquels on appartient, ce qui n'est pas le cas tout le temps :)

def ipv6_sans_masque(ipv6):
    """Supprime le /64 si présent (obligatoire pour BGP neighbor)"""
    return ipv6.split("/")[0]


def ebgpConfig(address1, 
               interface1,
               name1,
               as1, 
               address2, 
               interface2,
               name2,
               as2):
    
    neighbor_R1 = ipv6_sans_masque(address2)
    neighbor_R2 = ipv6_sans_masque(address1)

    commandes_1 = [
        "configure terminal",
        f"router bgp {as1}",
        f"bgp router-id {as1}.{as1}.{as1}.{as1}",
        "no bgp default ipv4-unicast",
        f"neighbor {neighbor_R1} remote-as {as2}",
        "address-family ipv6 unicast",
        f"neighbor {neighbor_R1} activate",
        "exit-address-family",
        "end"
    ]

    # =========================
    # Commandes R2
    # =========================
    commandes_2 = [

        "configure terminal",
        f"router bgp {as2}",
        f"bgp router-id {as2}.{as2}.{as2}.{as2}",
        "no bgp default ipv4-unicast",
        f"neighbor {neighbor_R2} remote-as {as1}",
        "address-family ipv6 unicast",
        f"neighbor {neighbor_R2} activate",
        "exit-address-family",
        "end"
    ]

    return commandes_1, commandes_2


#print(ebgpConfig("1001::1","g1/0","R1","1","1001:2","g1/0","R2","2"))

def ibgpConfig(routers, as_number, interface_loopback="Loopback0"):
    configs = {}

    for router in routers:
        name = router["name"]
        router_id = int(name[1:])

        commandes = [
            "enable",
            "configure terminal",
            f"router bgp {as_number}",
            f"bgp router-id {router_id}.{router_id}.{router_id}.{router_id}",
            "no bgp default ipv4-unicast"
        ]

        for other in routers:
            if other["name"] != name:
                other_ip = ipv6_sans_masque(other["loopback"])
                commandes += [
                    f"neighbor {other_ip} remote-as {as_number}",
                    f"neighbor {other_ip} update-source {interface_loopback}"
                ]

        commandes.append(" address-family ipv6 unicast")

        for other in routers:
            if other["name"] != name:
                other_ip = ipv6_sans_masque(other["loopback"])
                commandes.append(f"neighbor {other_ip} activate")

        commandes += [
            "exit-address-family",
            "end",
            " "
        ]

        configs[name] = commandes

    return configs

def redistribute_iBGP(as_number, igp, process_id): ## à faire que sur les routeurs de bordure pour annoncer les routes à BGP
    """
    Redistribue un IGP (OSPF ou RIP) dans BGP 
    """

    conf = [
        "enable",
        "configure terminal",
        f"router bgp {as_number}",
        "address-family ipv6 unicast"
    ]

    igp = igp.lower()

    if igp == "ospf":
        conf.append(f"redistribute ospf {process_id}")

    elif igp == "rip":
        conf.append(f"redistribute rip {process_id}")

    else:
        raise ValueError("IGP non supporté : utiliser 'ospf' ou 'rip'")

    conf += [
        "exit-address-family",
        "end",
        " "
    ]

    return conf


# address_blocked_list = 
# [
#     {"adress_blocked" : value , "for_who" : [addresses] }        addreses peut valoir "any"
#     {"adress_blocked" : value , "for_who" : [addresses] }
# ]



def create_access_list(address_blocked_list, name_acl, deny):     #deny = true => blocked address  deny = false => route autorisee
    conf = [
        "enable",
        "configure terminal",
        f"ipv6 access-list {name_acl} "
           ]
    for dico in address_blocked_list:
        for address in dico["for_who"]:
            if deny:
                conf.append(f"deny {dico["address_blocked"]} {address}")
            else:
                conf.append(f"permit {dico["address_blocked"]} {address}")
    #bonne pratique : conf.append("permit ipv6 any any")
    conf.append("end")
    conf.append(" ")
    return conf

def create_route_map(map_tag, name_acl, sequence_number, deny):
    conf = [
        "enable",
        "configure terminal"
           ]
    if deny:
        conf.append(f"route-map {map_tag} deny {sequence_number}")
    else:
        conf.append(f"route-map {map_tag} permit {sequence_number}")
    conf.append(f"match ipv6 address {name_acl}")
    conf.append("end")
    conf.append(" ")
    return conf