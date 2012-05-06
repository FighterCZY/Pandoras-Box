print 'started'

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Util.number import long_to_bytes, bytes_to_long

rsa = RSA.generate(1024)
username = 'abc123'

publicrsa = rsa.exportKey('OpenSSH')
privatersa = rsa.exportKey('PEM', 'PASSPHRASE')

print publicrsa

import xmlrpclib
s = xmlrpclib.ServerProxy('http://localhost:8000')
print s.registerUser(username, publicrsa)

from Crypto.Hash import MD5
def sign(data):
  hash = SHA.new(data).digest()
  (signature, ) = rsa.sign(hash, None)
  return long_to_bytes(signature)

data = "blahblahblah"
def addData(key, data):
  signature = sign(key)
  return s.addData(username, signature, key, data)

print addData("abc", data)
print addData("def", open('awefaf-0.enc').read())

signature = sign("abc")
print s.getData(username, signature, "abc")



raw_input("Press enter to quit\n")