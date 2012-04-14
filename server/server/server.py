import threading
import array
import hashlib
from System.Security.Cryptography import RSACryptoServiceProvider, CspParameters

import IsisWrapper as Isis
#import httpd
import RPC

cp = CspParameters();
cp.KeyContainerName = "PandorasKey"
RSA = RSACryptoServiceProvider(cp)
RSA.PersistKeyInCsp = True
#print RSA.ToXmlString(True);

def registerUser(username, publickey):
    res = []
    Isis.users.SafeQuery(Isis.Isis.Group.ALL, Isis.REGISTER_USER, username, publickey, Isis.Isis.EOLMarker(), res)
    print res
RPC.register_function(registerUser)

def getKey(key):
    x = Isis.dht.DHTGet(key)
    if x:
        return x
    else:
        return None
RPC.register_function(getKey)

def putKey(key, value):
    Isis.dht.DHTPut(key, value)
    return
RPC.register_function(putKey)

putKey("abc", "123")
print getKey("abc")

value = "blah blah"
key = "data/"+hashlib.sha1(value).hexdigest()
putKey(key, value)
print getKey(key)

'''
key = "users/test"
Isis.dht.DHTRemove(key)
print DHTGet(key)
'''


raw_input("Press enter to quit\n")