def ipv6_link_intra_as(router_a, router_b, num_as):
    id_a = int(''.join(filter(str.isdigit, router_a)))
    id_b = int(''.join(filter(str.isdigit, router_b)))

    low, high = sorted([id_a, id_b])
    prefix = f"fd{num_as}:{low}{high}::"

    return {
        router_a: f"{prefix}{id_a}/64",
        router_b: f"{prefix}{id_b}/64"
    }

def ipv6_link_inter_as(router_a, as_a, router_b, as_b):
    id_a = int(''.join(filter(str.isdigit, router_a)))
    id_b = int(''.join(filter(str.isdigit, router_b)))

    low_as, high_as = sorted([as_a, as_b])
    low_id, high_id = sorted([id_a, id_b])
    prefix = f"fd{low_as}{high_as}:{low_id}{high_id}::"

    return {
        router_a: f"{prefix}{id_a}/64",
        router_b: f"{prefix}{id_b}/64"
    }

def ipv6_loopback(nom_routeur, num_as):
    router_id = int(''.join(filter(str.isdigit, nom_routeur)))
    return f"fd{num_as}::{router_id}/128"

##addresses = ipv6_link_inter_as("R1",1,"R2",2)
##print(addresses)

# R1 = data["liens"][0]["from"]
# R2 = data["liens"][0]["to"]
# num_as = data["routeurs"][0]["as"]
# print(ipv6_link_intra_as(R1,R2,num_as))

