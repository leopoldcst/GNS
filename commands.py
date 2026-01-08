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


def ripConfig(address, interface, name):

    process_name = "RIP_AS"
    conf = []
    #conf += baseRouterConfig(name)
    #conf += addressConfig(interface,address)
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


def ospfConfig(address, interface, name, area_nb):
    conf = []
    process_id = int(name[1:])
    #conf += baseRouterConfig(name)
    #conf += addressConfig(interface,address)
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
        f" bgp router-id {as1}.{as1}.{as1}.{as1}",
        " no bgp default ipv4-unicast",
        f" neighbor {neighbor_R1} remote-as {as2}",
        " address-family ipv6 unicast",
        f"  neighbor {neighbor_R1} activate",
        " exit-address-family",
        "end"
    ]

    # =========================
    # Commandes R2
    # =========================
    commandes_2 = [

        "configure terminal",
        f"router bgp {as2}",
        f" bgp router-id {as2}.{as2}.{as2}.{as2}",
        " no bgp default ipv4-unicast",
        f" neighbor {neighbor_R2} remote-as {as1}",
        " address-family ipv6 unicast",
        f"  neighbor {neighbor_R2} activate",
        " exit-address-family",
        "end"
    ]

    return commandes_1, commandes_2


#print(ebgpConfig("1001::1","g1/0","R1","1","1001:2","g1/0","R2","2"))


    

    