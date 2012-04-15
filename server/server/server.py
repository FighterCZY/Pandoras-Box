import threading
import array
from Crypto.PublicKey import RSA

import IsisWrapper as Isis
#import httpd
import RPC

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

def checkSignature(username, signature, data):
    publickey = getKey("users/"+username)
    instance = RSA.importKey(publickey)
    return instance.verify(data, (signature,))

# RPC Functions

def registerUser(username, publickey):
    res = []
    Isis.users.SafeQuery(Isis.Isis.Group.ALL, Isis.REGISTER_USER, username, publickey, Isis.Isis.EOLMarker(), res)
    print res
RPC.register_function(registerUser)

def getUser(username):
    return getKey("users/"+str(username))
RPC.register_function(getUser)

def updateFile(username, signature, data):
    if not checkSignature(username, signature, data):
        return
    putKey("files/"+str(username), data)
RPC.register_function(updateFile)

def poll(username):
    return getKey("files/"+str(username))
RPC.register_function(poll)

def addData(username, signature, key, data):
    if not checkSignature(username, signature, key):
        return
    putKey("data/"+str(key), data)
RPC.register_function(addData)

def removeData(username, signature, key):
    if not checkSignature(username, signature, key):
        return
    removeKey("data/"+str(key))
RPC.register_function(removeData)

def getData(username, signature, key):
    if not checkSignature(username, signature, key):
        return
    return getKey("data/"+str(username)+"/"+str(key))
RPC.register_function(getData)

# test function
RPC.register_function(pow)


raw_input("Press enter to quit\n")