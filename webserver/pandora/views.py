from django.template import Context, loader
from django.shortcuts import render_to_response
from django.views.decorators.http import condition
from django.utils import simplejson
from django.http import HttpResponse

from Crypto.Hash import SHA

import xmlrpclib
import json
from rpccommunication import RPCCommunication


rpc = xmlrpclib.ServerProxy('http://localhost:8000')


def index(request):
  request.session['prime'] = 'primed'
  return render_to_response('pandora/index.html', {})

def register(request):
  output = ''
  username = request.GET.get('username')
  passphrase = request.GET.get('passphrase')
  
  if not username or not passphrase:
    return HttpResponse("No username/passphrase")
    
  
  output += "<p>Generating Key</p>"
  rpc = RPCCommunication()
  rpc.loadUser(username, passphrase)
  
  registeruser = rpc.registerUser()
  output += "<p>Register User: %s</p>" % registeruser
  if not registeruser:
    return HttpResponse("Username already taken")
  
  output += "<p>Register Key: %s</p>" % rpc.registerKey()
  
  request.session['username'] = username
  request.session['passphrase'] = passphrase
  request.session['rsa'] = rpc.exportKey()
  
  output += "<p>Registered User: '%s' with passphrase '%s'</p>" % (username, passphrase)
    
  return HttpResponse(output)

def login(request):
  username = request.GET.get('username')
  passphrase = request.GET.get('passphrase')
  
  if not username or not passphrase:
    return HttpResponse("No username/passphrase")
  
  rpc = RPCCommunication()
  try:
    rpc.loadUser(username, passphrase, existing=True)
  except:
    return HttpResponse("Invalid username or passphrase")
  
  request.session['username'] = username
  request.session['passphrase'] = passphrase
  request.session['rsa'] = rpc.exportKey()
  
  return HttpResponse("Logged in successfully '%s'" % request.session.get('username'))
  
@condition(etag_func=None)
def upload(request):
  def stream_response_generator():
    path = str(request.GET.get('path'))
    data = str(request.GET.get('data'))
    
    #path = "hello"
    #data = "world"
    key = SHA.new(path).hexdigest()
    
    if not path or not data:
      yield "No path/data"
      raise GeneratorExit
    
    rpc = loadRPC(request)
    files = rpc.poll()
    yield "<p>Polled</p>"
    yield " " * 1024  # Encourage browser to render incrementally
    
    yield "<p>Add data: %s</p>" % rpc.addData(key, data)

    if not files:
      files = ''
    files += "%s:%s\n" % (path, key)
    yield "<p>Update File: %s</p>" % rpc.updateFile(files)
  
  return HttpResponse( stream_response_generator(), mimetype='text/html')
  
def list(request):
  rpc = loadRPC(request)
  
  files = rpc.poll()
  if not files:
    return HttpResponse("No filelist for user")
    
  files = files.strip().split("\n")
  output = '<ul>';
  for f in files:
    path, key = f.split(':')
    output += "<li><a href='/show?filename=%s'>%s</a></li>" % (key, path)
  return HttpResponse(output)
  #return HttpResponse(simplejson.dumps(files), mimetype='application/json')
  
def show(request):
  filename = request.GET.get('filename');
  if not filename:
    return HttpResponse("Didn't specify filename")
  rpc = loadRPC(request)
  data = rpc.getData(filename)
  return HttpResponse(data)
  

# private functions
def loadRPC(request):
  username = request.session.get('username')
  passphrase = request.session.get('passphrase')
  rsa = request.session.get('rsa')
  
  if not username or not passphrase or not rsa:
    raise Exception("Not logged in")
  
  rpc = RPCCommunication()
  rpc.loadKey(username, passphrase, rsa)
  return rpc