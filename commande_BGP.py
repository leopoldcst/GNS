import json

FICHIER_JSON = "config_final_struct.json"


def trouver_as(data, nom_routeur):
    """Retourne le numéro d'AS d'un routeur"""
    for r in data["routeurs"]:
        if r["nom"] == nom_routeur:
            return r["as"]
    return None


def ipv6_sans_masque(ipv6):
    """Supprime le /64 si présent (obligatoire pour BGP neighbor)"""
    return ipv6.split("/")[0]


def BGP_commande(
    adresse_ipv6_R1, interface_R1, routeur_R1,
    adresse_ipv6_R2, interface_R2, routeur_R2
):

    with open(FICHIER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    as_R1 = trouver_as(data, routeur_R1)
    as_R2 = trouver_as(data, routeur_R2)

    if as_R1 is None or as_R2 is None:
        print("❌ Routeur non trouvé dans le JSON")
        return

    if as_R1 == as_R2:
        print("❌ BGP inter-AS uniquement (AS identiques)")
        return

    lien_ok = False
    for lien in data["liens"]:
        if lien["type"] == "inter-as":
            if (
                (lien["from"] == routeur_R1 and lien["to"] == routeur_R2) or
                (lien["from"] == routeur_R2 and lien["to"] == routeur_R1)
            ):
                lien_ok = True
                break

    if not lien_ok:
        print("❌ Aucun lien inter-AS entre ces routeurs")
        return


    neighbor_R1 = ipv6_sans_masque(adresse_ipv6_R2)
    neighbor_R2 = ipv6_sans_masque(adresse_ipv6_R1)

    # =========================
    # Commandes R1
    # =========================
    commandes_1 = [
        "enable",
        "configure terminal",
        "ipv6 unicast-routing",
        f"interface {interface_R1}",
        " ipv6 enable",
        f" ipv6 address {adresse_ipv6_R1}",
        " no shutdown",
        " exit",
        f"router bgp {as_R1}",
        f" bgp router-id {as_R1}.{as_R1}.{as_R1}.{as_R1}",
        " no bgp default ipv4-unicast",
        f" neighbor {neighbor_R1} remote-as {as_R2}",
        " address-family ipv6 unicast",
        f"  neighbor {neighbor_R1} activate",
        " exit-address-family",
        "end"
    ]

    # =========================
    # Commandes R2
    # =========================
    commandes_2 = [
        "enable",
        "configure terminal",
        "ipv6 unicast-routing",
        f"interface {interface_R2}",
        " ipv6 enable",
        f" ipv6 address {adresse_ipv6_R2}",
        " no shutdown",
        " exit",
        f"router bgp {as_R2}",
        f" bgp router-id {as_R2}.{as_R2}.{as_R2}.{as_R2}",
        " no bgp default ipv4-unicast",
        f" neighbor {neighbor_R2} remote-as {as_R1}",
        " address-family ipv6 unicast",
        f"  neighbor {neighbor_R2} activate",
        " exit-address-family",
        "end"
    ]

    print(f"\n### Configuration BGP sur {routeur_R1} ###")
    for cmd in commandes_1:
        print(cmd)

    print(f"\n### Configuration BGP sur {routeur_R2} ###")
    for cmd in commandes_2:
        print(cmd)

    return commandes_1,commandes_2



BGP_commande(
    "1000:0:0:15::1/64", "GigabitEthernet2/0", "R1",
    "1000:0:0:15::2/64", "GigabitEthernet2/0", "R5"
)
