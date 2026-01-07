def baseRouterConfig(name):
    return [
        "enable",
        "configure terminal",
        f"hostname {name}",
        "ipv6 unicast-routing",
        "end"
    ]

def addressConfig(interface,address): ## pas sûr à revoir 
    return [
        "enable",
        "configure terminal",
        f"interface {interface}",
        " ipv6 enable",
        f" ipv6 address {address}",
        " no shutdown",
        " exit",
        "end"
    
    ]

# il faut reprendre OSPF, RIP, BGP ici en simplifiant toutes les fonctions et en utilisant celles du dessus ! 