import threading
import clr
import hashlib
import os
import cPickle as pickle # alternatively pickle

# add ISIS
clr.AddReference("isis2")

from System import Environment
from System import Array, Func, Action
#Environment.SetEnvironmentVariable("ISIS_TCP_ONLY", "true")
Environment.SetEnvironmentVariable("ISIS_UNICAST_ONLY", "true")
# Silence output
Environment.SetEnvironmentVariable("ISIS_MUTE", "true")
# add comma separated list of hosts here (master servers)
Environment.SetEnvironmentVariable("ISIS_HOSTS", "Abigail")
import Isis
from Isis import *

IsisSystem.Start()
print('Isis started')

class IsisImplementation():
    # Isis function constants
    REGISTER_USER = 0

    def __init__(self):
        self.__initdht__();
        self.__initusers__();

    def __initdht__(self):
        self.dht = Group('DHT')


        # this is already locked by ISIS
        DHTDict = dict()
        def DHTWriterMethod(key, value):
            parts = str(key).split('/')
            #if parts[0] == 'users':
            #    DHTDict[key] = value
            if parts[0] == 'keys':
                DHTDict[key] = value
            elif parts[0] == 'files':
                DHTDict[key] = value
            elif parts[0] == 'data':
                dir = os.path.dirname(key)
                if not os.path.exists(dir):
                    os.makedirs(dir)
                with open(str(key), 'w') as f:
                    f.write(str(value))

        def DHTReaderMethod(key):
            parts = str(key).split('/')
            #if parts[0] == 'users':
            #    return DHTDict.get(key)
            if parts[0] == 'keys':
                return DHTDict.get(key)
            elif parts[0] == 'files':
                return DHTDict.get(key)
            elif parts[0] == 'data':
                try:
                    with open(str(key), 'r') as f:
                        return f.read()
                except IOError:
                    return null

        def DHTKeysMethod():
            files = []
            for d in os.listdir('data'):
                files.append('data/'+d)
            return Array[object](DHTDict.keys() + files) # TODO: add disk files

        self.dht.SetDHTPersistenceMethods(Group.DHTPutMethod(DHTWriterMethod), Group.DHTGetMethod(DHTReaderMethod), Group.DHTKeysMethod(DHTKeysMethod))

        self.dht.DHTEnable(1, 1, 1) # For debug only
        #self.dht.DHTEnable(3, 6, 6) # For production testing


        def myViewFunc(v):
            if v.IAmLeader():
                print('New view: ' + v.ToString())
            print('My rank = ' + v.GetMyRank().ToString())
            for a in v.joiners:
                print(' Joining: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
            for a in v.leavers:
                print(' Leaving: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
            return
        self.dht.RegisterViewHandler(ViewHandler(myViewFunc))
        self.dht.Join()
    
    def __initusers__(self):
        self.users = Group('users')
        # check that a username is valid and not taken
        self.users_lock = threading.Lock()
        self.users_list = dict()
        # return True if able to register user
        def registerUser(username, publickey):
            with self.users_lock:
                in_table = username in self.users_list
                if in_table:
                    reply = False
                else:
                    self.users_list[username] = publickey
                    reply = True
            self.users.Reply(reply)
        self.users.RegisterHandler(self.REGISTER_USER, Action[str, str](registerUser))


        def loadUsers(serial):
            # because isis uses a weird serializer Y U NO PROTOCOLBUFFER/THRIFT?!?!
            set = pickle.loads(serial)
            with self.users_lock:
                # do an update in case we got some stuff before the master replied
                self.users_list.update(set)
            print 'loaded users'
            return
        self.users.RegisterLoadChkpt(Action[str](loadUsers))

        def sendUsers(view):
            with self.users_lock:
                data = pickle.dumps(self.users_list)
            self.users.SendChkpt(data)
            self.users.EndOfChkpt()
        self.users.RegisterMakeChkpt(Isis.ChkptMaker(sendUsers))

        # Don't print anything. DHT group already prints stuff
        def myViewFunc(v):
            return
        self.users.RegisterViewHandler(ViewHandler(myViewFunc))

        self.users.Join()

    # Public Methods
    def registerUser(self, username, publickey):
        res = []
        # reserves the username by checking if its already taken
        self.users.SafeQuery(Group.ALL, self.REGISTER_USER, username, publickey, EOLMarker(), res)
        # returns whether they all succeeded
        success = (min(res) == True)
        return success

    def getUserKey(self, username):
        with self.users_lock:
            return self.users_list.get(username)

    def getKey(self, key):
        x = self.dht.DHTGet(key)
        if x:
            return x
        else:
            return None

    def putKey(self, key, value):
        self.dht.DHTPut(key, value)
        return

    def removeKey(self, key):
        self.dht.DHTRemove(key)
        return

_impl = IsisImplementation()
registerUser = _impl.registerUser
getUserKey = _impl.getUserKey
getKey = _impl.getKey
putKey = _impl.putKey
removeKey = _impl.removeKey

t = threading.Thread(target=IsisSystem.WaitForever)
t.daemon = True
t.start()