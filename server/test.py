print 'started'

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Util.number import long_to_bytes, bytes_to_long

rsa = RSA.generate(1024)
username = 'abc'

publicrsa = rsa.exportKey('OpenSSH')
privatersa = rsa.exportKey('PEM', 'PASSPHRASE')

print publicrsa

import xmlrpclib
s = xmlrpclib.ServerProxy('http://localhost:8000')
print s.registerUser(username, publicrsa)

data = "blahblahblah"
def addData(data):
  key = SHA.new(data).hexdigest()
  (signature, ) = rsa.sign(key, None)
  signature = long_to_bytes(signature)
  return s.addData(username, signature, key, data)

#print addData(data)
(signature, ) = rsa.sign("abc", None)
signature = long_to_bytes(signature)
print s.getData(username, signature, "abc")



raw_input("Press enter to quit\n")