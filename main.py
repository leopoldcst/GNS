import json

FICHIER_JSON = "config_final_struct.json"

with open(FICHIER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

def create_commandes():
    for links in data["liens"]:
                routeur1 = links["from"]
                routeur2 = links["to"]
                interface_from = links["interface_from"]
                interface_to = links["interface_to"]
                if links["type"]=="intra-as":
                    for elt in data["routeurs"]:
                        if elt["nom"]==routeur1:
                            num_as = elt["as"]

    if num_as == 1 :
        rip_commandes("1000:0:0:1::1/64",interface_from,routeur1,routeur2)
        print()
        rip_commandes("1000:0:0:1::2/64",interface_to,routeur2,routeur1)
        print()
    if num_as == 2 :
        ospf_commandes("1000:0:0:1::1/64",interface_from,routeur1,routeur2)
        print()
        ospf_commandes("1000:0:0:1::2/64",interface_to,routeur2,routeur1)
        print()