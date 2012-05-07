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
import chunkcrypter as cc
from chunkcrypter import bufferDir
import shutil
from Crypto.Hash import SHA

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

''' OBSERVER >o'''
class observerEventHandler(FileSystemEventHandler):
    def __init__(self, ignore_patterns=None, patterns=None):
        super(observerEventHandler, self).__init__()
        self._ignore_patterns = ignore_patterns
        self._patterns = patterns
     
    @property
    def ignore_patterns(self):
        return self._ignore_patterns
    
    @property
    def patterns(self):
        return self._patterns
    
    """Handle all the events captured."""
#    def on_moved(self, event):
#        super(observerEventHandler, self).on_moved(event)
#        what = 'directory' if event.is_directory else 'file'
#        logging.info("Moved %s: from %s to %s", what, event.src_path, event.dest_path)
#        print '=============================================='
#        print 'Moved ', what, ': ', event.src_path
#        synchronizeRemote()
 
#    def on_created(self, event):
#        super(observerEventHandler, self).on_created(event)
#        what = 'directory' if event.is_directory else 'file'
#        print '=============================================='
#        print 'Created ', what, ': ', event.src_path
#        synchronizeRemote()
#
#    def on_deleted(self, event):
#        super(observerEventHandler, self).on_deleted(event)
#        what = 'directory' if event.is_directory else 'file'
#        print '=============================================='
#        print 'Deleted ', what, ': ', event.src_path
#        synchronizeRemote() 
#    def on_modified(self, event):
#        super(observerEventHandler, self).on_modified(event)
#        what = 'directory' if event.is_directory else 'file'
#        print '=============================================='
#        print 'Modified ', what, ': ', event.src_path
#        synchronizeRemote()
    def on_any_event(self, event):
        global syncingLocal
        if not syncingLocal:
            pprint.pprint('Synchronize Remote')
            synchronizeRemote()
         
    def dispatch(self, event):  
        if has_attribute(event, 'dest_path'):
            paths = [event.src_path, event.dest_path]
        else:
            paths = [event.src_path]
        if match_any_paths(paths, 
                           included_patterns=self.patterns, 
                           excluded_patterns=self.ignore_patterns):
            self.on_any_event(event)

''' GLOBALS ''' 
username = ''
event_handler = observerEventHandler(ignore_patterns=['*'+bufferDir+'*','*chunkcrypter.py*','*observer.py*'], 
                                     patterns=['*/pbox/*'])
#event_handler = observerEventHandler(set(['*'+bufferDir+'*']))
observer = Observer() 
observer.schedule(event_handler, path='.', recursive=True)    

''' BEGIN FILE EVENTLISTENER '''
def monitor():
    counter = 0
    observer.start() 
    try:
        while True:
            time.sleep(1)
            counter = (counter + 1) % 10
            if counter == 0:
                synchronizeLocal()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

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
    remoteState = cc.getRemoteState()
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
        cc.addFileFromRemote(fileToAdd, localState, remoteState)
def deleteRemoteFromLocal(filesToDelete, localState, remoteState): # delete each file in deletedFiles from local directory
    for deletedFile in filesToDelete:
        fdelete(deletedFile)

''' LOCAL MODIFICATION: UPDATE REMOTE '''
def synchronizeRemote(): # Synchronize remote state with local state
    remoteState = cc.getRemoteState()
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
            print 'Adding ' + fileToAdd + ' to remote...'
            cc.addFileToRemote(fileToAdd, localState, remoteState)
    print 'Done adding local to remote...'
def deleteLocalFromRemote(filesToDelete, localState, remoteState): # delete each file in deletedFiles from remote directory
    for fileToDelete in filesToDelete:
        cc.deleteFileFromRemote(fileToDelete, localState, remoteState)
    print 'Done deleting local from remote...'

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
    print 'Touching bufferDir'
    touchDirectory(bufferDir)
    
    print 'Connecting...'
    cc.connect()

if __name__ == "__main__":
    initialize()
    monitor()
#    synchronizeLocal()
    
    
    pass
 