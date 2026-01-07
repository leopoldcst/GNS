import json
import gns
import commands

FICHIER_JSON = "config_final_struct.json"

if __name__ == "__main__":
    # Reading the intent file
    f = open(FICHIER_JSON, "r", encoding="utf-8")
    intent = json.load(f)
    f.close()


    g = gns.GnsProject(name=intent["project_name"])

    g.createNew(autoRecover=True)
    g.open()

    print("Opened the project")

    for router in intent["routers"]:
        name = router["name"]

        print(f"Creating router {name}")
        g.createRouter(name=name, autoRecover=True)

        print("Configuring the router")
        routerSocket = gns.RouterSocket(port=g.getRouterPort(name))
        for cmd in commands.baseRouterConfig(name):
            routerSocket.run(cmd)

        routerSocket.close()

    #for link in intent["links"]:
    #    print(f"Adding link from {link["from"]} to {link["to"]}")
    #    try:
    #        g.createLink(link["from"],
    #                    link["interface_from"],
    #                    link["to"],
    #                    link["interface_to"])
    #    except:
    #        print("Link already exists")

    #    if link["type"] == "intra-as":
    #        for router in intent["routers"]:
    #            if router["name"] == link["from"]:
    #                if link[""]

    #                rip_commandes("1000:0:0:1::1/64", link["from_interface"], link["from"], link["to"])

    #        # Implement rip or opsf
    #        pass
    #    elif link["type"] == "inter-as":
    #        # Implement bgp
    #        pass
            
          #  if num_as == 1 :
              #  rip_commandes("1000:0:0:1::1/64",interface_from,routeur1,routeur2)
              #  print()
              #  rip_commandes("1000:0:0:1::2/64",interface_to,routeur2,routeur1)
              #  print()
          #  if num_as == 2 :
              #  ospf_commandes("1000:0:0:1::1/64",interface_from,routeur1,routeur2)
              #  print()
              #  ospf_commandes("1000:0:0:1::2/64",interface_to,routeur2,routeur1)
              #  print()
    
    ## g.recoverRouter(name="R1")

    # print(tn.read_all().decode('ascii'))

    # g.close()

    # g = GnsProject(name="Test")
    # g.createNew()
    # g.recoverExisting()
    # g.recoverRouter(name="R3")
    # port = g.getRouterPort("R3")

    # routerS = RouterSocket(port=port)
    # routerS.run("configure terminal")
    # routerS.run("interface g1/0")
    # routerS.run("ipv6 enable")
    # routerS.close()
