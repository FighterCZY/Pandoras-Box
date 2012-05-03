'''
Created on Mar 23, 2012

@author: lisherwin
''' 
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.randpool import RandomPool
import sys, os, errno, glob
import shutil, struct
import pickle
import re, random

root = 'pbox/'

keyDir = root + '.ssh'
keyPublic = keyDir + '/public.pem'
keyPrivate = keyDir + '/private.pem'

metadataDir = root + '.metadata'
metadataRemoteState = metadataDir + '/state'

bufferDir = root + '.blockbuffer'

import observer5 as obs

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
def fdeletefolder(name):
    try:
        shutil.rmtree(name)
    except:
        pass
        #print 'Could not find folder: ', name
def fdeletefile(name): 
    try: 
        os.remove(name)
    except:
        pass
        #print 'Could not find file: ', name
def fdelete(name):
    fdeletefolder(name)
    fdeletefile(name)
def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise
def touchDirectory(string):
    mkdir(string)
def touchFile(fname, times = None):
    with file(fname, 'a'):
        os.utime(fname, times)
        
''' Chunk ''' 
def chunk(fileName):
    touchDirectory(bufferDir)
    doChunk(fileName)     
def doChunk(fileName, chunk_size=1024):
 
    ''' Fill buffer directory with fileName contents '''
    file_object = fopen(fileName)
    chunk_count = 0
    data = file_object.read(chunk_size)
    basename = os.path.basename(fileName)
    while data:
        chunkFile = fwrite(''.join([bufferDir,'/',basename,'-',str(chunk_count)]))
        chunkFile.write(data)
        data = file_object.read(chunk_size)
        chunk_count = chunk_count + 1
def doChunkCryptPreview(fileName, chunk_size=1024):
    file_object = fopen(fileName)
    chunk_count = 0
    data = file_object.read(chunk_size)
    chunkList = [] 
    while data:
        chunkList.append(fileName + '-' + str(chunk_count) + '.enc')
        chunk_count = chunk_count + 1
        data = file_object.read(chunk_size)
    return chunkList
    
def cleanBuffer():
    fdelete(bufferDir)

''' RSA Keys '''
def generatePrivPubKey(prefix=''):
    private = RSA.generate(1024)
    public = private.publickey()
    publicKeyFile = fwrite(keyPublic)
    privateKeyFile = fwrite(keyPrivate)
    publicKeyFile.write(public.exportKey())
    privateKeyFile.write(private.exportKey())
    return private, public
def pubKeyExists():
    return fexists(keyPublic)
def privKeyExists():
    return fexists(keyPrivate)
def getPubKey():
    return fopen(keyPublic)
def getPrivKey():
    return fopen(keyPrivate)
def getFilesToEncrypt(path):
    base = os.path.basename(path)
    fileNames = glob.glob(bufferDir+'/'+base+'*')
    return fileNames
def getFilesToDecrypt(path):
    base = os.path.basename(path)
    fileNames = glob.glob(bufferDir+'/'+base+'*.enc')
    return fileNames

''' RSA '''
def encrypt_file(key, in_filename, out_filename=None, chunksize=1024):
    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)
                outfile.write(encryptor.encrypt(chunk))
def decrypt_file(key, in_filename, out_filename=None, chunksize=1024):
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0]

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)
def encrypt(path):
    filesToEncrypt = getFilesToEncrypt(path)
    for fileToEncrypt in filesToEncrypt:
        encrypt_file('0123456789abcdef', fileToEncrypt, fileToEncrypt+'.enc')
def decrypt(path):
    filesToDecrypt = getFilesToDecrypt(path)
    for fileToDecrypt in filesToDecrypt:
        decrypt_file('0123456789abcdef', fileToDecrypt, fileToDecrypt.rstrip('.enc'))
        fdelete(fileToDecrypt)
    
def tryint(s):
    try:
        return int(s)
    except:
        return s
def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]
def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)
    
def mergeBuffer(destination):
    filesToMerge = glob.glob(bufferDir + '/*')
    sort_nicely(filesToMerge)
    destinationFile = fwrite(destination)
    for fileToMerge in filesToMerge:
        contents = fopen(fileToMerge).read()
        destinationFile.write(contents)
    destinationFile.close()
    
''' RPC Calls '''
def addFileFromRemote(fileName):
    pass
def deleteFileFromRemote(fileName):
    pass
def addFileToRemote(fileName):
    chunk(fileName)
    encrypt(fileName)
    print 'Sending off ... ', fileName # Send it off!
    cleanBuffer()
def getRemoteDirectoryState():
    pass # poll()

''' Tests Faking RPC Calls '''
remoteDir = 'remote'
remoteState = remoteDir + '/state'

def initializeRemote():
    touchDirectory(remoteDir)
    touchFile(remoteState)
    
def getRemoteDirectoryStateFake():
    try:
        return pickle.load(fopen(remoteState))
    except:
        print 'Remote directory does not hold state. Initializing now.'
        initializeRemote()
        pickle.dump({}, fwrite(remoteState))        
        return {}

def updateRemoteState(state):
    remoteStateFile = fwrite(remoteState)
    pickle.dump(state, remoteStateFile)

''' <<<<<<<- '''
def getFileFromRemote(chunkCryptToRequestFromRemote, chunk_size=1024):
    return fopen(remoteDir + '/' + chunkCryptToRequestFromRemote).read()
def addFileFromRemoteFake(path, localState, remoteState, chunk_size=1024):
    chunkCryptsToRequestFromRemote = []
    if remoteState.has_key(path):
        chunkCryptsToRequestFromRemote = remoteState[path]['files']
    for chunkCryptToRequestFromRemote in chunkCryptsToRequestFromRemote:
        contents = getFileFromRemote(chunkCryptToRequestFromRemote)
        touchDirectory(bufferDir)
        basename = os.path.basename(chunkCryptToRequestFromRemote)
        chunkCryptFileOnLocal = fwrite(bufferDir + '/' + basename)
        chunkCryptFileOnLocal.write(contents)
        chunkCryptFileOnLocal.close()
    decrypt(path)
    mergeBuffer(path)
    cleanBuffer()
        
def deleteFileInLocal(path, localState, remoteState):
    fdelete(path)

''' ->>>>>>> '''    
def addFileToRemoteFake(path, localState, remoteState):
    deleteFileFromRemoteFake(path, localState, remoteState)
    chunk(path)
    encrypt(path)
    
    baseLocal = os.path.basename(path)
    dirLocal = os.path.dirname(path) + '/'
    
    bufferDirFiles = glob.glob(''.join([bufferDir,'/',baseLocal,'-*.enc']))
    for bufferDirFileName in bufferDirFiles:
        obs.touchRecursiveDirectory(remoteDir + '/' + dirLocal)
        
        remoteDirFileName = remoteDir + '/' + dirLocal + os.path.basename(bufferDirFileName)
        remoteDirFile = fwrite(remoteDirFileName)
        
        bufferDirFile = fopen(bufferDirFileName)
        
        print 'writing ', bufferDirFileName, ' to ', remoteDirFileName
        remoteDirFile.write(bufferDirFile.read())
    cleanBuffer()
def deleteFileFromRemoteFake(path, localState, remoteState):
    if remoteState.has_key(path):
        filesToDelete = remoteState[path]['files']
        for fileToDelete in filesToDelete:
            fdelete(remoteDir + '/' + fileToDelete)
    