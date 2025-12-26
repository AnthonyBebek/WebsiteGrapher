'''
This script is used as a dependancy for the URLServer.py file, if you are running this program as a client only, then it's safe to delete it

This script keeps track of the clients connected to the network
'''
import random
import string
import datetime

class Client:
    clients = {}
    free_ids = set()

    def __init__(self, LastHeartbeat, ClientIP, client_id = None):
        if client_id != None:
            self.ClientNumber = client_id
        else:
            self.ClientNumber = self.RegisterNewClientNumber()
        self.LastHeartbeat = LastHeartbeat
        self.ClientIP = ClientIP

        Client.clients[self.ClientNumber] = self

    def RegisterNewClientNumber(self, client_id = None):
        if Client.free_ids:
            return Client.free_ids.pop()
        else:
            while True:
                if client_id == None:
                    client_id = self.generate_short_uuid()
                if client_id not in Client.clients:
                    return client_id

    def generate_short_uuid(self):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(4))

    def UpdateHeartbeat(self):
        self.LastHeartbeat = datetime.datetime.now()

    def ReleaseClientNumber(self):
        if self.ClientNumber in Client.clients:
            del Client.clients[self.ClientNumber]
            Client.free_ids.add(self.ClientNumber)

    @classmethod
    def GetClient(cls, ClientNumber):
        return cls.clients.get(ClientNumber)

    @classmethod
    def GetClients(cls):
        return list(cls.clients.values())
    
    @classmethod
    def GetClientCount(cls):
        return len(cls.clients)