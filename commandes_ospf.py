# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 16:36:39 2025

@author: Hugo
"""
import json

FICHIER_JSON = "config_final_struct.json"


def ospf_commandes(addresse_ipv6,interface,nom_routeur):
    # Charger le JSON
    with open(FICHIER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    ROUTEUR_CIBLE = "R3"   # <- change ici si besoin avec une fonction qui creer les liens demandés
    # Trouver le routeur cible
    routeur = None
    for r in data["routeurs"]:
        if r["nom"] == ROUTEUR_CIBLE:
            routeur = r
            break

    if routeur is None:
        print("Routeur non trouvé")
        return

    commandes = []
    process_id = int(nom_routeur[1:])
    for ro in data["routeurs"]:
        if ro["nom"] == nom_routeur:
            area_nb = ro["as"]
            break
    

    
    # Début configuration
    commandes.append("enable")
    commandes.append("configure terminal")
    
    # Nom du routeur
    commandes.append(f"hostname {nom_routeur}")

    # IPv6 global
    commandes.append("ipv6 unicast-routing")
    commandes.append(f"ipv6 router ospf {process_id}")
    commandes.append(f"router-id {process_id}.{process_id}.{process_id}.{process_id}")
    commandes.append(f"interface {interface}")
    commandes.append(" ipv6 enable")
    commandes.append(f" ipv6 address {addresse_ipv6}")
    commandes.append(" no shutdown")
    commandes.append(f" ipv6 ospf {process_id} area {area_nb}")
    commandes.append(" end")

    
    
    # Affichage (ou écriture fichier)
    for cmd in commandes:
        print(cmd)

       '''
       fin programme OSPF
       début programme RIP 
       ''' 
        
def rip_commandes(addresse_ipv6,interface, nom_routeur):
    # Charger le JSON
    with open(FICHIER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

  
    ROUTEUR_CIBLE = "R3"   # <- change ici si besoin avec une fonction qui creer les liens demandés
    #exemple :
    #for r in data["liens"]:
    #    if r["from"] == nom_routeur:
    #        ROUTEUR_CIBLE = r["to"]
    #        break
    
    # Trouver le routeur cible
    routeur = None
    for r in data["routeurs"]:
        if r["nom"] == ROUTEUR_CIBLE:
            routeur = r
            break

    if routeur is None:
        print("Routeur non trouvé")
        return

    commandes = []
    process_name = "RIP_AS"
    
    # Début configuration
    commandes.append("enable")
    commandes.append("configure terminal")
    
    # Nom du routeur
    commandes.append(f"hostname {nom_routeur}")

    # IPv6 global
    commandes.append("ipv6 unicast-routing")
    
    commandes.append(f"interface {interface}")
    commandes.append(" ipv6 enable")
    commandes.append(f" ipv6 address {addresse_ipv6}")
    commandes.append(" no shutdown")
    commandes.append(f"ipv6 router rip {process_name}")
    #commandes.append(" redistribute connected") à activer si on veut partager tous les sous reseaux auxquels on appartient, ce qui n'est pas le cas tout le temps :)
    commandes.append(" exit")
    commandes.append(f"interface {interface}")
    commandes.append(f"ipv6 rip {process_name} enable")
    commandes.append(" end")

    
    
    # Affichage (ou écriture fichier)
    for cmd in commandes:
        print(cmd)

rip_commandes("1000:0:0:1::2/64","g1/0","R3")
rip_commandes("1000:0:0:1::1/64","g1/0","R4")
#rip_commandes("1000:0:0:2::1/64","g2/0","R3")