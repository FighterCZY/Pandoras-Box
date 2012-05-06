import clr
import sys

print sys.path #get load paths
clr.AddReference("IronPyCrypto")

import threading
import array
from Crypto.PublicKey import RSA
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Hash import SHA

import IsisWrapper as Isis
#import httpd
import RPC


def checkSignature(username, signature, data):
    publickey = Isis.getUserKey(username)
    instance = RSA.importKey(publickey)
    hash = SHA.new(data).digest()
    return instance.verify(hash, (bytes_to_long(signature),))

# RPC Functions
class RPCFunctions:
    def registerUser(self, username, publickey):
        """ Register a username and publickey.
        Returns True if success, False otherwise
        """
        return Isis.registerUser(username, publickey)

    def registerKey(self, username, signature, privatekey):
        """ Register a private key with a user
        Requires signature of privatekey
        Returns True if success, False otherwise
        """
        if not checkSignature(username, signature, privatekey):
            print "invalid signature"
            return False
        Isis.putKey(("keys/%s" % username), privatekey)
        return True

    def getUser(self, username):
        """ Get public key of user
        Returns publickey
        """
        return Isis.getUserKey(username)

    def getKey(self, username):
        """ Get the (encrypted) private key of the user
        Returns privatekey
        """
        return Isis.getKey("keys/%s" % username)

    def updateFile(self, username, signature, data):
        """ Update file list of user
        Requires signature of data
        Data should be encrypted
        Returns True if success, False otherwise
        """
        if not checkSignature(username, signature, data):
            return False
        Isis.putKey(("files/%s" % username), data)
        return True

    def poll(self, username):
        """ Get file list of user
        Returns filelist (encrypted) if success, False otherwise
        """
        return Isis.getKey("files/%s" % username)

    def addData(self, username, signature, key, data):
        """ Add a block of data to a user
        Requires signature of key
        Key should be unique reference for block (sha1 hash)
        Data should be encrypted
        Returns True if success, False otherwise
        """
        if not checkSignature(username, signature, key):
            return False
        Isis.putKey(("data/%s/%s" % (username, key)), data)
        return True

    def removeData(self, username, signature, key):
        """ Remove a block of data from user
        Requires signature of key
        Returns True if success, False otherwise
        """
        if not checkSignature(username, signature, key):
            return False
        Isis.removeKey("data/%s/%s" % (username, key))
        return True

    def getData(self, username, signature, key):
        """ Get a block of data from user
        Requires signature of key
        Returns data if success, False otherwise
        """
        if not checkSignature(username, signature, key):
            return False
        return Isis.getKey("data/%s/%s" % (username, key))

RPC.register_instance(RPCFunctions())

# test function
RPC.register_function(pow)


raw_input("Press enter to quit\n")