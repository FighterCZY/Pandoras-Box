'''
Created on Mar 23, 2012

@author: lisherwin
''' 
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Hash import SHA
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Util.randpool import RandomPool
import sys, os, errno, glob
import shutil, struct
import pickle
import re, random
import pprint
from rpccommunication import RPCCommunication
from base64 import b64encode, b64decode

serverIP = 'http://128.84.203.136:8000'

username = 'lisherwin4'
passphrase = 'wuzhang'

root = 'pbox/'

bufferDir = root + '.blockbuffer'

rpool = RandomPool() 
rpc = RPCCommunication()

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
def fdeletefile(name): 
    try: 
        os.remove(name)
    except:
        pass
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

def hash(path):
    return SHA.new(path).hexdigest()

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
    print 'Cleaning buffer...'
    fdelete(bufferDir)

'''RPC Calls'''
def initRemoteState():
    if rpc.poll() == False:
        print 'Initializing remote state...'
        updateRemoteState({})
    else:
        print 'Remote state already initialized...'
def connect():
    global rpc
    try: 
        rpc.loadUser(username, passphrase, True)
        print 'Existing user!'
    except:
        print 'New user!'
        rpc.loadUser(username, passphrase, False)
        rpc.registerUser()
        rpc.registerKey()
    
    initRemoteState()
    
''' RSA Keys '''
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
''' Helpers '''
def getRemoteState():
    return pickle.loads(b64decode(rpc.poll()))
def updateRemoteState(state):
    rpc.updateFile(b64encode(pickle.dumps(state)))
    
''' <<<<<<<- '''
def receiveChunks(path, localState, remoteState):
    paths = []
    if remoteState.has_key(path):
        paths = remoteState[path]['files']
    for path in paths:
        # Receive key/value
        key = hash(path)
        value = rpc.getData(key)
        contents = b64decode(value) 
        
        # Prepare output
        touchDirectory(bufferDir)
        basename = os.path.basename(path)
        chunkCryptFileOnLocal = fwrite(bufferDir + '/' + basename) 
        
        # Write to output
        chunkCryptFileOnLocal.write(contents) 
        chunkCryptFileOnLocal.close()
def addFileFromRemote(path, localState, remoteState):
    receiveChunks(path, localState, remoteState)
    decrypt(path)
    mergeBuffer(path)
    cleanBuffer()
def deleteFileFromRemote(path, localState, remoteState):
    rpc.removeData(hash(path))
''' ->>>>>>> '''
def sendOffChunks(path):
    # Get files to send off in bufferDir
    recFileName = os.path.basename(path)
    bufferPaths = glob.glob(bufferDir + '/' + recFileName + '-*.enc')
    
    # Send off each file
    for bufferPath in bufferPaths:
        
        # Create key 
        dir = os.path.dirname(path)
        base = os.path.basename(bufferPath)
        path = dir + '/' + base
        print 'Encryption block fullpath: '+ path
        key = hash(path)
        print 'Key: ' + key
        
        # Create value
        bufferDirFile = fopen(bufferPath)
        value = b64encode(bufferDirFile.read())
        print 'Value: ' + value
        
        # Send off key/value
        rpc.addData(key, value)
def addFileToRemote(path, localState, remoteState):
    chunk(path)
    encrypt(path)
    print 'Encrypting ' + path
    sendOffChunks(path)
    cleanBuffer()    
def deleteFileInLocal(path, localState, remoteState):
    fdelete(path)
