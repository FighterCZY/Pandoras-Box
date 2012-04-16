import threading
from DocXMLRPCServer import DocXMLRPCServer, DocXMLRPCRequestHandler
from SocketServer import ThreadingMixIn

class ThreadingServer(ThreadingMixIn, DocXMLRPCServer):
    pass

#server = DocXMLRPCServer.DocXMLRPCServer(("", 8000), requestHandler = RequestHandler, logRequests=False)
# debug with logging
#server = DocXMLRPCServer.DocXMLRPCServer(("", 8000), requestHandler = RequestHandler)
server = ThreadingServer(('', 8000), DocXMLRPCRequestHandler)
server.register_introspection_functions()

def register_function(fun):
    server.register_function(fun)
def register_instance(instance):
    server.register_instance(instance)

t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()