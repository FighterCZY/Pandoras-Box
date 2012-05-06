from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto import Random
from Crypto.Util.number import long_to_bytes, bytes_to_long
from base64 import b64encode, b64decode

import xmlrpclib

class RPCCommunication():
  #initialize and load/generate a key
  def __init__(self, username, passphrase, existing=False):
    self.rpc = xmlrpclib.ServerProxy('http://localhost:8000')
    self.username = username
    self.passphrase = passphrase
    if existing:
      key = self.rpc.getKey(self.username)
      self.rsa = RSA.importKey(key, passphrase)
    else:
      self.rsa = RSA.generate(1024)

  def registerUser(self):
    publicrsa = self.rsa.exportKey('OpenSSH')
    return self.rpc.registerUser(self.username, publicrsa)
    
  def registerKey(self):
    privatersa = self.rsa.exportKey('PEM', self.passphrase)
    return self.rpc.registerKey(self.username, self.sign(privatersa), privatersa)
    
  def updateFile(self, data):
    data = self.encrypt(data)
    return self.rpc.updateFile(self.username, self.sign(data), data)
    
  def poll(self):
    return self.decrypt(self.rpc.poll(self.username))
    
  def addData(self, key, data):
    return self.rpc.addData(self.username, self.sign(key), key, self.encrypt(data))
    
  def removeData(self, key):
    return self.rpc.removeData(self.username, self.sign(key), key)
    
  def getData(self, key):
    return self.decrypt(self.rpc.getData(self.username, self.sign(key), key))
  
  
  # private/seldom used functions  
  def sign(self, data):
    # returns a signature of data
    hash = SHA.new(data).digest()
    (signature, ) = self.rsa.sign(hash, None)
    return long_to_bytes(signature)

  def encrypt(self, data):
    (encrypted, ) = self.rsa.encrypt(data, None)
    return b64encode(encrypted)

  def decrypt(self, data):
    if not data:
      return False
    # add randfunc if doesn't exist
    if not self.rsa._randfunc:
      self.rsa._randfunc = Random.new().read
    return self.rsa.decrypt(b64decode(data))