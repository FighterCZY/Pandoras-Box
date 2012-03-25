'''
Created on Mar 23, 2012

@author: lisherwin
''' 
from Crypto.PublicKey import RSA
from Crypto.Util.randpool import RandomPool
import sys, os, errno, glob
import shutil
REMOTE_DIR_SNAPSHOT_FILE = 'directoryDict'
BUFFER_DIR = 'blockbuffer'
rpool = RandomPool() 

def fopen(name): 
    return open(name)
def fappend(name):
    return open(name, 'a')
def fwrite(name):
    return open(name, 'w')
def fexists(filename):
    try: 
        open(filename)
        return True
    except IOError as e:
        return False

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise
        
# Consider tempfile.mkdtemp()
def touchDirectory(string):
    mkdir(string)

def clearDirectory(string):
    shutil.rmtree(string)

def doChunk(fileName, chunk_size=1024):
#def doChunk(fileName, chunk_size=1048576):
    file_object = fopen(fileName)
    chunk_count = 0
    data = file_object.read(chunk_size)
    while data:
        chunkFile = fwrite(''.join(['.hidden/',fileName,'-',str(chunk_count)]))
        chunkFile.write(data)
        data = file_object.read(chunk_size)
        chunk_count = chunk_count + 1

def chunk(fileName):
    touchDirectory('.hidden')
    doChunk(fileName) 

def clean():
    clearDirectory('.hidden')

def generatePrivPubKey(prefix=''):
    private = RSA.generate(1024)
    public = private.publickey()
    publicKeyFile = fwrite(prefix+'public.pem')
    privateKeyFile = fwrite(prefix+'private.pem')
    publicKeyFile.write(public.exportKey())
    privateKeyFile.write(private.exportKey())
    return private, public

def getRSAPubKey():
    return fopen('public.pem').read()

def getRSAPrivKey():
    return fopen('private.pem').read()

def getEncryptionFiles(fileName):
    fileNames = glob.glob(''.join(['.hidden/',fileName,'*']))
    return fileNames

def encrypt(fileName):
    filesToEncrypt = getEncryptionFiles(fileName)
    if not fexists('server.public.pem'):
        print 'We do not have your Pandora\'s box public key. TODO: Send request for PB public key!'
    else:
        encrypter = RSA.importKey(fopen('server.public.pem').read())
        for fileName in filesToEncrypt:
            encFile = fwrite(fileName + '.enc')
            encryptedText = encrypter.encrypt(fopen(fileName).read(),0)[0]
            encFile.write(encryptedText)
            
def decrypt(fileName):
    fileToDecrypt = fopen(fileName)
    if not fexists('private.pem'):
        print 'We cannot find your Pandora\'s box private key. Not authorized!'
    else:
        decrypter = RSA.importKey(fopen('private.pem').read())
        outputFile = fwrite(fileName + '.dec')
        outputFile.write(decrypter.decrypt(fileToDecrypt.read()))

def serverDecrypt(fileName):
    fileToDecrypt = fopen(fileName)
    if not fexists('server.private.pem'):
        print 'Server does not have private.pem!'
    else:
        decrypter = RSA.importKey(fopen('server.private.pem').read())
        outputFile = fwrite(fileName + '.dec')
        outputFile.write(decrypter.decrypt(fileToDecrypt.read()))
        
def copyAll():
    touchDirectory('backup')
    clearDirectory('backup')
    shutil.copytree('.hidden', 'backup')

#if __name__ == '__main__':
def chunkcrypt(fileName='Ignorance.mp3'):
    
    chunk(fileName)
    
    encrypt(fileName)
    
    print 'Sending off ... ', fileName # Send it off!
    
    copyAll() # Testing
    
    clean()