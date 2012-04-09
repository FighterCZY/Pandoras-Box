import clr
clr.AddReference('isis2.dll')
import Isis
from Isis import *

import threading

IsisSystem.Start()
print('Isis started')

def myfunc(i):
    print('Hello from myfunc with i=' + i.ToString())
    return
def myRfunc(r):
    print('Hello from myRfunc with r=' + r.ToString())
    g.Reply(-1)
    return
def myViewFunc(v):
    print('New view: ' + v.ToString())
    print('My rank = ' + v.GetMyRank().ToString())
    for a in v.joiners:
        print(' Joining: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    for a in v.leavers:
        print(' Leaving: ' + a.ToString() + ', isMyAddress='+a.isMyAddress().ToString())
    return

g = Group('FooBar')
g.RegisterHandler(0, IsisDelegate[int](myfunc))
g.RegisterHandler(1, IsisDelegate[float](myRfunc))
g.RegisterViewHandler(ViewHandler(myViewFunc))
g.Join()
g.Send(0, 17)
res = []
nr = g.Query(Group.ALL, 1, 98.8, EOLMarker(), res);
print('After Query got ' + nr.ToString() + ' results: ', res)
res2 = []
nr = g.Query(Group.ALL, 0, 98, EOLMarker(), res2);
print('After Query got ' + nr.ToString() + ' results: ', res2)


t = threading.Thread(target=IsisSystem.WaitForever)
t.daemon = True
t.start()
print('Hello world')
raw_input('Press enter to quit')