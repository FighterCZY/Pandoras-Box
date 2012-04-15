import threading
import array
from System.Security.Cryptography import RSACryptoServiceProvider, CspParameters

import IsisWrapper as Isis
#import httpd
import RPC

cp = CspParameters();
cp.KeyContainerName = "PandorasKey"
RSA = RSACryptoServiceProvider(cp)
RSA.PersistKeyInCsp = True
#print RSA.ToXmlString(True);


def getKey(key):
    x = Isis.dht.DHTGet(key)
    if x:
        return x
    else:
        return None

def putKey(key, value):
    Isis.dht.DHTPut(key, value)
    return

def removeKey(key):
    Isis.dht.DHTRemove(key)
    return

def checkSignature(publickey, signature, data):
    pass

# RPC Functions

def registerUser(username, publickey):
    res = []
    Isis.users.SafeQuery(Isis.Isis.Group.ALL, Isis.REGISTER_USER, username, publickey, Isis.Isis.EOLMarker(), res)
    print res
RPC.register_function(registerUser)

def getUser(username):
    return getKey("users/"+str(username))
RPC.register_function(getUser)

# TODO: add signature checking on data
def updateFile(username, signature, data):
    putKey("files/"+str(username), data)
RPC.register_function(updateFile)

def poll(username):
    return getKey("files/"+str(username))
RPC.register_function(poll)

# TODO: add signature checking on key
def addData(username, signature, key, data):
    putKey("data/"+str(key), data)
RPC.register_function(addData)

# TODO: add signature checking on key
def removeData(username, signature, key):
    removeKey("data/"+str(key))
RPC.register_function(removeData)

def getData(username, key):
    return getKey("data/"+str(username)+"/"+str(key))
RPC.register_function(getData)

# test function
RPC.register_function(pow)


raw_input("Press enter to quit\n")