import time
import xmlrpclib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.utils import has_attribute
from pathtools.patterns import match_any_paths
import logging
import sys
import hashlib 
import os, errno
import pprint
import pickle
import chunkcrypter5 as cc
from chunkcrypter5 import bufferDir
from chunkcrypter5 import keyDir
import shutil


syncingLocal = False

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
def touchRecursiveDirectory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

''' GET STATE '''
def getLocalDirectoryState(path=cc.root):
    directories = {}
    directoryTuples = os.walk(path)
    for dirname, dirnames, filenames in directoryTuples:
        remove_hidden(dirnames) # dynamically changing dirnames so that directoryTuples will reflect removal of all hidden directories
        for subdirname in dirnames:
            directories[os.path.join(dirname, subdirname)] = None
        for filename in filenames:
            if not filename.startswith('.'): # remove all hidden files
                path = os.path.join(dirname, filename)
                directories[path] = {} 
                directories[path]['md5'] = md5_for_file(os.path.join(dirname, filename))
                directories[path]['files'] = cc.doChunkCryptPreview(path)
    return directories
def remove_hidden(dirlist): # in-place modification of dirlist
    dirlist[:] = [d for d in dirlist if not d.startswith('.')]
def md5_for_file(fileName, block_size=2**20):
    f = fopen(fileName)
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()

''' POLL: UPDATE LOCAL '''
def synchronizeLocal(): # Synchronize local state with remote state 
    global syncingLocal
    syncingLocal = True
    remoteState = cc.getRemoteDirectoryStateFake()
    localState = getLocalDirectoryState()
    print 'Local State:'
    pprint.pprint(localState)
    print 'Remote State:'
    pprint.pprint(remoteState)
    
    addedFiles, modifiedFiles, deletedFiles = compareStates(localState, remoteState)
    print 'Updating local directory <<<<<<<<-'
    print addedFiles
    print '\twere added in remote directory.'
    print modifiedFiles
    print '\twere modified in remote directory.'
    print deletedFiles
    print '\twere deleted in remote directory.'
      
    addRemoteToLocal(addedFiles, localState, remoteState) 
    addRemoteToLocal(modifiedFiles, localState, remoteState)
    deleteRemoteFromLocal(deletedFiles, localState, remoteState)
    syncingLocal = False
def addRemoteToLocal(filesToAdd, localState, remoteState): # make RPC function calls to get blocks from remote
    for fileToAdd in filesToAdd:
        cc.addFileFromRemoteFake(fileToAdd, localState, remoteState)
def deleteRemoteFromLocal(filesToDelete, localState, remoteState): # delete each file in deletedFiles from local directory
    for deletedFile in filesToDelete:
        fdelete(deletedFile)

''' LOCAL MODIFICATION: UPDATE REMOTE '''
def synchronizeRemote(): # Synchronize remote state with local state
    remoteState = cc.getRemoteDirectoryStateFake()
    localState = getLocalDirectoryState()
    
    addedFiles, modifiedFiles, deletedFiles = compareStates(remoteState, localState)
    
    print 'Updating remote directory ->>>>>>>>>'
    print addedFiles
    print '\t being pushed to remote directory.'
    print modifiedFiles
    print '\t being pushed to remote directory.'
    print deletedFiles
    print '\t being deleted from remote directory.'
    
    addLocalToRemote(addedFiles, localState, remoteState)
    addLocalToRemote(modifiedFiles, localState, remoteState)
    deleteLocalFromRemote(deletedFiles, localState, remoteState)
    cc.updateRemoteState(localState)
def addLocalToRemote(filesToAdd, localState, remoteState): # make RPC function calls to put blocks to remote
    for fileToAdd in filesToAdd:
        if os.path.isfile(fileToAdd):
            cc.addFileToRemoteFake(fileToAdd, localState, remoteState)
def deleteLocalFromRemote(filesToDelete, localState, remoteState): # delete each file in deletedFiles from remote directory
    for fileToDelete in filesToDelete:
        cc.deleteFileFromRemoteFake(fileToDelete, localState, remoteState)

''' STATE COMPARISON '''
def getAddedFiles(oldDirectory, currentDirectory):
    addedFiles = []
    for path,info in currentDirectory.iteritems():
        if not oldDirectory.has_key(path) and not info is None: # if old directory does not have path, but new one does, then a file has been added.
            print path, 'added.'
            addedFiles.append(path)
    return addedFiles
def getModifiedFiles(oldDirectory, currentDirectory):
    modifiedFiles = []
    for path,info in currentDirectory.iteritems():
        if oldDirectory.has_key(path) and not info is None:
            if not oldDirectory[path]['md5'] == info['md5']:
                print path, 'contents modified.'
                modifiedFiles.append(path)
    return modifiedFiles
def getDeletedFiles(oldDirectory, currentDirectory):
    deletedFiles = []
    for path,hash in oldDirectory.iteritems():
        if not currentDirectory.has_key(path): # if old directory has a path, but new one doesn't, then a file has been deleted.
            print path, 'deleted.'
            deletedFiles.append(path)
    return deletedFiles
def compareStates(oldState, newState):
    addedFiles = getAddedFiles(oldState, newState)
    modifiedFiles = getModifiedFiles(oldState, newState)
    deletedFiles = getDeletedFiles(oldState, newState)
    return addedFiles, modifiedFiles, deletedFiles

def initialize():
    touchDirectory(keyDir)
    touchDirectory(bufferDir)

if __name__ == "__main__":
    initialize()
    synchronizeLocal()
#    synchronizeRemote()
    
    pass
 