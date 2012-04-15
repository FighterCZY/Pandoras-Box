import threading
import DocXMLRPCServer
#import SimpleXMLRPCServer

class RequestHandler(DocXMLRPCServer.DocXMLRPCRequestHandler):
    pass

#server = DocXMLRPCServer.DocXMLRPCServer(("", 8000), requestHandler = RequestHandler, logRequests=False)
# debug with logging
server = DocXMLRPCServer.DocXMLRPCServer(("", 8000), requestHandler = RequestHandler)
server.register_introspection_functions()

def register_function(fun):
    server.register_function(fun)

t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()