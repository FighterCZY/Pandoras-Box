import time
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
from chunkcrypter import REMOTE_DIR_SNAPSHOT_FILE
from chunkcrypter import BUFFER_DIR
EVENT_TYPE_MOVED = 'moved'
EVENT_TYPE_DELETED = 'deleted'
EVENT_TYPE_CREATED = 'created'
EVENT_TYPE_MODIFIED = 'modified'

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

def pathexists(path):
    return os.path.exists(path)    
    
def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise
        
def md5_for_file(fileName, block_size=2**20):
    f = fopen(fileName)
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.digest()

def touchDirectory(string): 
    mkdir(string)

def remove_hidden(dirlist): # in-place modification of dirlist
    dirlist[:] = [d for d in dirlist if not d.startswith('.')]

def hidden(string):
    parts = string.split('/')
    parts[0] = parts[0].startswith('.')
    return reduce(lambda x, y: x or y.startswith('.'), parts)

def getCurrentDirectory(path='.'):
    directories = {}
    directoryTuples = os.walk(path)
    for dirname, dirnames, filenames in directoryTuples:
#        pprint.pprint(dirname) pprint.pprint(dirnames) pprint.pprint(filenames)
        remove_hidden(dirnames) # dynamically changing dirnames so that directoryTuples will reflect removal of all hidden directories
        for subdirname in dirnames:
            directories[os.path.join(dirname, subdirname)] = None
        for filename in filenames:
            if not filename.startswith('.'): # remove all hidden files
                directories[os.path.join(dirname, filename)] = md5_for_file(os.path.join(dirname, filename))
    return directories

def storeDirectory(directoryDict):
    touchDirectory('.metadata')
    pickle.dump(directoryDict, fwrite('.metadata/'+REMOTE_DIR_SNAPSHOT_FILE))

def updatePrevious():
    storeDirectory(getCurrentDirectory())

def getPreviousDirectory():
    return pickle.load(fopen('.metadata/'+REMOTE_DIR_SNAPSHOT_FILE))

def checkForAddModify(currentDirectory, oldDirectory):
    for path,hash in currentDirectory.iteritems():
        if not oldDirectory.has_key(path):
            print path, 'added.'
            cc.chunkcrypt(path)
        else:
            if not oldDirectory[path] == hash:
                print path, 'contents modified.'
                cc.chunkcrypt(path)

def checkForDelete(currentDirectory, oldDirectory):
    for path,hash in oldDirectory.iteritems():
        if not currentDirectory.has_key(path):
            print path, 'deleted.'
            print 'Notifying server of file delete ...'

def synchronize():
    compareDirectories()
    updatePrevious()

def compareDirectories(currentDirectory=None, oldDirectory=None):
    if currentDirectory == None:
        currentDirectory = getCurrentDirectory()
    if oldDirectory == None:
        oldDirectory = getPreviousDirectory()
        
    checkForAddModify(currentDirectory, oldDirectory)
    checkForDelete(currentDirectory, oldDirectory)

class observerEventHandler(FileSystemEventHandler):
    def __init__(self, ignore_patterns=None):
        super(observerEventHandler, self).__init__()
        self._ignore_patterns = ignore_patterns
    
    @property
    def ignore_patterns(self):
        return self._ignore_patterns
    
    """Handle all the events captured."""
    def on_moved(self, event):
        super(observerEventHandler, self).on_moved(event)
        what = 'directory' if event.is_directory else 'file'
        logging.info("Moved %s: from %s to %s", what, event.src_path, event.dest_path)
        synchronize()

    def on_created(self, event):
        super(observerEventHandler, self).on_created(event)
        what = 'directory' if event.is_directory else 'file'
        logging.info("Created %s: %s", what, event.src_path)
        synchronize()

    def on_deleted(self, event):
        super(observerEventHandler, self).on_deleted(event)
        what = 'directory' if event.is_directory else 'file'
        logging.info("Deleted %s: %s", what, event.src_path)
        synchronize()

    def on_modified(self, event):
        super(observerEventHandler, self).on_modified(event)
        what = 'directory' if event.is_directory else 'file'
        logging.info("Modified %s: %s", what, event.src_path)
        synchronize()
        
    def dispatch(self, event):
        if has_attribute(event, 'dest_path'):
            paths = [event.src_path, event.dest_path]
        else:
            paths = [event.src_path]
            
        if match_any_paths(paths, excluded_patterns=self.ignore_patterns):
            self.on_any_event(event)
            _method_map = {
                EVENT_TYPE_MODIFIED: self.on_modified,
                EVENT_TYPE_MOVED: self.on_moved,
                EVENT_TYPE_CREATED: self.on_created,
                EVENT_TYPE_DELETED: self.on_deleted,
            }
            event_type = event.event_type 
            _method_map[event_type](event) 
         
event_handler = observerEventHandler(set(['*'+REMOTE_DIR_SNAPSHOT_FILE,'*'+BUFFER_DIR+'*','*chunkcrypter.py*','*observer.py*']))
observer = Observer() 
observer.schedule(event_handler, path='.', recursive=True) 

if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO)
    synchronize()
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    pass
 