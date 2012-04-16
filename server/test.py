print 'started'

from Crypto.PublicKey import RSA

key = RSA.generate(1024)

publickey = key.exportKey('OpenSSH')
privatekey = key.exportKey('PEM', 'PASSPHRASE')

import xmlrpclib
s = xmlrpclib.ServerProxy('http://localhost:8000')
print s.registerUser('abc', publickey)


raw_input("Press enter to quit\n")