def type_to_number(intent, type):
    if type == "client":
        return intent["valueCommunity"]["client"]
    if type == "peer":
        return intent["valueCommunity"]["peer"]
    if type == "provider":
        return intent["valueCommunity"]["provider"] 
    
def community_number(as_number, number): ## number = value if it is a client, provider, peer
    return f"{as_number}:{number}"

