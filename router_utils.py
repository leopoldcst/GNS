class Router:
    def __init__(self, intent, name):
        self.as_nb = intent["routers"]["name"]["as"]
        self.name = name
        self.id = self.name[1:]
        self.cmds = []