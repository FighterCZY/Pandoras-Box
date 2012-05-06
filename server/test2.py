from rpccommunication import RPCCommunication

rpc = RPCCommunication("username", "passphrase")

print rpc.registerUser()
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