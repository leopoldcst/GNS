### Implémenter le démarrage du routeur


#Ajouter : link_style: Optional[Any] = None dans la library gns3fy


from gns3fy import gns3fy, Project, Node, Link
import telnetlib3.telnetlib as telnetlib

import datetime


class GnsProject:
    def __init__(self, ip="http://localhost", port=3080, name="Test project") -> None:
        self.name = name
        self.routers = {}

        self.server = gns3fy.Gns3Connector(f"{ip}:{str(port)}")
        self.lab = gns3fy.Project(name=self.name, connector=self.server)


    def createNew(self, autoRecover=False):
        if autoRecover:
            if self.server.get_project(self.name) is not None:
                self.recoverExisting()

                return
        self.lab.create()


    def recoverExisting(self):
        self.lab.get()
        

    def open(self):
        self.lab.open()


    def close(self):
        self.lab.close()


    def createRouter(self, name="Router", model="c7200", autoRecover=False):
        if autoRecover:
            for node in self.lab.nodes:
                if node.name == name:
                    self.recoverRouter(name, model)

                    return
        
        router = Node(
            project_id=self.lab.project_id,
            connector=self.server,
            name=name,
            template=model
        )

        router.create()

        self.routers[name] = router


    def recoverRouter(self,  name="Router", model="c7200"):
        router = Node(
            project_id=self.lab.project_id,
            connector=self.server,
            name=name,
            template=model
        )

        router.get()

        self.routers[name] = router


    def getRouterInterface(self, router_name, port_name):
        if port_name is None:
            print("ERROR Please give at least one type of name")

            return None
        
        for port in self.routers[router_name].ports:
            if port["name"] == port_name or port["short_name"] == port_name:
                return {"adapter": port["adapter_number"], "port": port["port_number"]}
            

    def createLink(self, r1_name, r1_port_name, r2_name, r2_port_name):
        r1_interface = self.getRouterInterface(r1_name, r1_port_name)
        r2_interface = self.getRouterInterface(r2_name, r2_port_name)

        nodes = [
            dict(node_id=self.routers[r1_name].node_id,
                 adapter_number=r1_interface["adapter"],
                 port_number=r1_interface["port"]),
            dict(node_id=self.routers[r2_name].node_id,
                 adapter_number=r2_interface["adapter"],
                 port_number=r2_interface["port"]),
        ]
        
        link = Link(project_id=self.lab.project_id, connector=self.server, nodes=nodes)
        link.create()


    def getRouterPort(self, router_name):
        return self.routers[router_name].console



class RouterSocket:
    def __init__(self, host="localhost", port=0) -> None:
        self.tn = telnetlib.Telnet(host, port)
        self.run("\r")
        

    def run(self, command):
        self.tn.write(command.encode("ascii")+b"\r")


    def close(self):
        self.tn.close()
        


if __name__ == "__main__":
    g = GnsProject(name=round(datetime.datetime.now().timestamp()))
    # g.recoverExisting()
    
    g.createNew()
    g.createRouter(name="R1")
    g.createRouter(name="R3")
    g.createRouter(name="R2")
    g.createLink("R1", "g1/0", "R2", "g2/0")
    g.createLink("R2", "g1/0", "R3", "g2/0")

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

