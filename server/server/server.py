import threading
import clr
import hashlib
import os
import array
import cPickle as pickle # alternatively pickle
from System import Func, Action

# add ISIS
clr.AddReference('isis2.dll')
from System import Environment
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


dht = Group('DHT')

# this is already locked by ISIS
DHTDict = dict()
def DHTWriterMethod(key, value):
    parts = str(key).split('/')
    if parts[0] == 'users':
        DHTDict[key] = value
    elif parts[0] == 'files':
        return #IMPLEMENT ME
    elif parts[0] == 'data':
        hex = hashlib.sha1(value).hexdigest()
        # Ensure that the location is a sha1 of the value
        if parts[1] == hex:
            # Create directory if does't exist
            dir = os.path.dirname(key)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(str(key), 'w') as f:
                f.write(str(value))

def DHTReaderMethod(key):
    parts = str(key).split('/')
    if parts[0] == 'users':
        return DHTDict.get(key)
    elif parts[0] == 'files':
        return #IMPLEMENT ME
    elif parts[0] == 'data':
        try:
            with open(str(key), 'r') as f:
                return f.read()
        except IOError:
            return null

def DHTKeysMethod():
    return DHTDict.keys() # TODO: add disk files

dht.SetDHTPersistenceMethods(Group.DHTPutMethod(DHTWriterMethod), Group.DHTGetMethod(DHTReaderMethod), Group.DHTKeysMethod(DHTKeysMethod))

dht.DHTEnable(1, 1, 1) # For debug only
#dht.DHTEnable(3, 6, 6) # For production testing


def myfunc(i):
    print('Hello from myfunc with i=' + i.ToString())
    return
def myRfunc(r):
    print('Hello from myRfunc with r=' + r.ToString())
    dht.Reply(-1)
    return

dht.RegisterHandler(0, IsisDelegate[int](myfunc))
#dht.RegisterHandler(1, IsisDelegate[float](myRfunc))


def myViewFunc(v):
    if v.IAmLeader():
        print('New view: ' + v.ToString())
    print('My rank = ' + v.GetMyRank().ToString())
    for a in v.joiners:
        print(' Joining: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    for a in v.leavers:
        print(' Leaving: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    return
dht.RegisterViewHandler(ViewHandler(myViewFunc))
dht.Join()

# res = []
# nr = dht.Query(Group.ALL, 1, 98.8, EOLMarker(), res);
# print('After Query got ' + nr.ToString() + ' results: ', res)
# res2 = []
# nr = dht.Query(Group.ALL, 0, 98, EOLMarker(), res2);
# print('After Query got ' + nr.ToString() + ' results: ', res2)


g = Group('all')
REGISTER_USER = 0
SEND_USERS = 1
# check that a username is valid and not taken
users_lock = threading.Lock()
users = set()
# return True if able to register user
def registerUser(username, publickey):
    with users_lock:
        in_table = username in users
    if in_table:
        g.Reply(False)
    else:
        # add username and bytes used
        dht.DHTPut('users/'+username, pickle.dumps(publickey, 0))
        with users_lock:
            users.add(username)
        g.Reply(True)
g.RegisterHandler(REGISTER_USER, IsisDelegate[str, str](registerUser))


def loadUsers(serial):
    # because isis uses a weird serializer Y U NO PROTOCOLBUFFER/THRIFT?!?!
    set = pickle.loads(serial)
    with users_lock:
        # do an update in case we got some stuff before the master replied
        users.update(set)
    print 'loaded users'
    return
g.RegisterLoadChkpt(IsisDelegate[str](loadUsers))

def sendUsers(view):
    with users_lock:
        data = pickle.dumps(users)
    g.SendChkpt(data)
    g.EndOfChkpt()
g.RegisterMakeChkpt(Isis.ChkptMaker(sendUsers))

def myViewFunc(v):
    if v.IAmLeader():
        print('New view: ' + v.ToString())
    print('My rank = ' + v.GetMyRank().ToString())
    for a in v.joiners:
        print(' Joining: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    for a in v.leavers:
        print(' Leaving: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    return
g.RegisterViewHandler(ViewHandler(myViewFunc))

g.Join()

dht.Send(0, 17)


res = []
g.Query(Group.ALL, REGISTER_USER, "newuser", "pubkey", EOLMarker(), res)
print res


def DHTGet(key):
    x = dht.DHTGet(key)
    if x:
        return x
    else:
        return None

dht.DHTPut("abc", "123")
print DHTGet("abc")

value = "blah blah"
key = "data/"+hashlib.sha1(value).hexdigest()
dht.DHTPut(key, value)
print DHTGet(key)

key = "users/test"
dht.DHTRemove(key)
print DHTGet(key)


t = threading.Thread(target=IsisSystem.WaitForever)
t.daemon = True
t.start()
raw_input('Press enter to quit')