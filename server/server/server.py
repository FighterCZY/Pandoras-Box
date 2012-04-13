import threading
import clr
import hashlib
import os
import array
import cPickle as pickle # alternatively pickle

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


g = Group('FooBar')

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
g.SetDHTPersistenceMethods(Group.DHTPutMethod(DHTWriterMethod), Group.DHTGetMethod(DHTReaderMethod))

g.DHTEnable(1, 1, 1) # For debug only
#g.DHTEnable(3, 6, 6) # For production testing


def myfunc(i):
    print('Hello from myfunc with i=' + i.ToString())
    return
def myRfunc(r):
    print('Hello from myRfunc with r=' + r.ToString())
    g.Reply(-1)
    return

#g.RegisterHandler(0, IsisDelegate[int](myfunc))
#g.RegisterHandler(1, IsisDelegate[float](myRfunc))


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
        g.DHTPut('users/'+username, (publickey, 0))
        with users_lock:
            users.add(username)
        g.Reply(True)
g.RegisterHandler(REGISTER_USER, IsisDelegate[str, str](registerUser))

def sendUsers(serial):
    # because isis uses a weird serializer Y U NO PROTOCOLBUFFER/THRIFT?!?!
    set = pickle.loads(serial)
    with users_lock:
        # do an update in case we got some stuff before the master replied
        users.update(set)
    return
g.RegisterHandler(SEND_USERS, IsisDelegate[str](sendUsers))

def myViewFunc(v):
    if v.IAmLeader():
        print('New view: ' + v.ToString())
    print('My rank = ' + v.GetMyRank().ToString())
    for a in v.joiners:
        print(' Joining: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
        # send the new joiner the userstable
        with users_lock:
            data = pickle.dumps(users)
        g.P2PSend(a, SEND_USERS, data)
    for a in v.leavers:
        print(' Leaving: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    return
g.RegisterViewHandler(ViewHandler(myViewFunc))
g.Join()
# g.Send(0, 17)
# res = []
# nr = g.Query(Group.ALL, 1, 98.8, EOLMarker(), res);
# print('After Query got ' + nr.ToString() + ' results: ', res)
# res2 = []
# nr = g.Query(Group.ALL, 0, 98, EOLMarker(), res2);
# print('After Query got ' + nr.ToString() + ' results: ', res2)


def DHTGet(key):
    x = g.DHTGet(key)
    if x:
        return x
    else:
        return None

g.DHTPut("abc", "123")
print DHTGet("abc")

value = "blah blah"
key = "data/"+hashlib.sha1(value).hexdigest()
g.DHTPut(key, value)
print DHTGet(key)



t = threading.Thread(target=IsisSystem.WaitForever)
t.daemon = True
t.start()
raw_input('Press enter to quit')