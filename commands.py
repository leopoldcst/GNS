def baseRouterConfig(name):
    return [
        "enable",
        "configure terminal",
        f"hostname {name}",
        "ipv6 unicast-routing"
    ]