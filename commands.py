def base_router_config(name):
    return [
        "enable",
        "configure terminal",
        f"hostname {name}",
        "ipv6 unicast-routing",
        "end"
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
        "enable",
        "configure terminal",
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


def bgp_config(router_id, as_nb):
    return [
        f"configure terminal",
        f"router bgp {as_nb}", # Enters BGP configuration
        f"bgp router-id {router_id}.{router_id}.{router_id}.{router_id}",
        f"no bgp default ipv4-unicast",
        f"end"]

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


def e_bgp_neighbor_config(as_nb, neighbor_ip, neighbor_as_nb):
    return [
        f"configure terminal",
        f"router bgp {as_nb}", # Enters BGP configuration
        f"neighbor {neighbor_ip} remote-as {neighbor_as_nb}", # Enters neighbor config
        f"address-family ipv6 unicast",
        f"neighbor {neighbor_ip} activate",
        f"exit-address-family", ### !!! Maybe is useless because of the end command
        f"end"]


def whole_as_i_bgp_config(routers, as_nb, local_loopback_name="Loopback0"):
    all_cmds = {}

    for router in routers:
        name = router["name"]
        router_id = int(name[1:])

        cmds = [
            "enable",
            "configure terminal",
            f"router bgp {as_nb}",
        ]

        # Add all the other routers of the AS to the iBGP config on our router
        for other in routers:
            if other["name"] == name:
                continue

            other_ip = other["loopback"].split("/")[0]
            cmds += [
                f"neighbor {other_ip} remote-as {as_nb}",
                f"neighbor {other_ip} update-source {local_loopback_name}"
                f"neighbor {other_ip} activate"
            ]

        commandes += [
            "exit-address-family",
            "end"
        ]

        all_cmds[name] = cmds

    return all_cmds

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



# def create_route_map(map_tag, name_acl, sequence_number, deny=True):
#     conf = [
#         "enable",
#         "configure terminal"
#     ]

#     action = "deny" if deny else "permit"
#     conf.append(f"route-map {map_tag} {action} {sequence_number}")
#     conf.append(f" match ipv6 address {name_acl}")

#     # obligatoire sinon ils les deny all
#     conf.append(f"route-map {map_tag} permit {sequence_number + 10}")

#     conf += [
#         "end",
#         " "
#     ]

#     return conf

def create_route_map(map_tag, sequence_number=10, name_acl=None, deny=False, community=None):
    conf = [
        "enable",
        "configure terminal"
    ]

    action = "deny" if deny else "permit"

    conf.append(f"route-map {map_tag} {action} {sequence_number}")

    if name_acl:
        conf.append(f"match ipv6 address {name_acl}")

    if community:
        if deny:
            raise ValueError(
                "Impossible de définir une community dans une route-map deny")
        conf.append(f"set community {community}")

    conf.append(f"route-map {map_tag} permit {sequence_number + 10}")

    conf += [
        "end",
        " "
    ]

    return conf


def apply_route_map(address, map_tag, as_number, entry=True):
    conf = []
    conf += [
        "enable",
        "configure terminal",
        f"router bgp {as_number}",
        "address-family ipv6 unicast"
             ]
    if entry:
        conf.append(f"neighbor {address} route-map {map_tag} in")
    else:
        conf.append(f"neighbor {address} route-map {map_tag} out")

    conf.append("end")
    conf.append("")
    return conf


def enable_community(): # à faire sur tous les routeurs pour qu'ils comprennent quand on fait  f" set community {community}"
    return [
        "enable",
        "configure terminal",
        "ip bgp-community new-format",
        "end",
        " "
    ]

def create_community_list(name, community, permit=True):

    action = "permit" if permit else "deny"

    return [
        "enable",
        "configure terminal",
        f"ip community-list standard {name} {action} {community}",
        " "
    ]


#################################################################
#Comment initialiser une community et appliquer une règle dessus#
#################################################################

## Je fais un premier create_route_map puis apply_route_map 
# qui tag toutes les routes. Après je créé la community-list lié 
# avec le numéro de community puis j'applique la règle que je veux



    












    


