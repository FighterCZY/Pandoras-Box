from rpccommunication import RPCCommunication

rpc = RPCCommunication()
rpc.loadUser("username", "passphrase")

print rpc.getUser("username")
print rpc.registerUser()
print rpc.getUser("username")
print rpc.registerKey()
print rpc.addData("somehash", "123")
poll = rpc.poll()
print poll #should print False
if not poll:
  poll = ''
poll += "abc:somehash\n"
print rpc.updateFile(poll)
print rpc.getData("somehash")
print rpc.removeData("somehash")
print rpc.getData("somehash") #should print False
print rpc.poll()

raw_input("Press enter to quit\n")