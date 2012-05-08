from django.template import Context, loader
from django.shortcuts import render_to_response
from django.views.decorators.http import condition
from django.utils import simplejson
from django.http import HttpResponse

from Crypto.Hash import SHA

import hashlib
import xmlrpclib
import json, pickle
from base64 import b64encode, b64decode
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
    
    if not path or not data:
      yield "No path/data"
      raise GeneratorExit
      
    file = "%s-0" % path
    key = SHA.new(file).hexdigest()
    
    rpc = loadRPC(request)
    files = rpc.poll()
    if files:
      dict = pickle.loads(b64decode(files.strip()))
    else:
      dict = dict()
    yield "<p>Polled</p>"
    yield " " * 1024  # Encourage browser to render incrementally
    
    yield "<p>Add data: %s</p>" % rpc.addData(key, data)

    dict[path] = {'files': [file], 'md5': md5_for_string(data)}
    
    files = b64encode(pickle.dumps(dict))
    yield "<p>Update File: %s</p>" % rpc.updateFile(files)
  
  return HttpResponse( stream_response_generator(), mimetype='text/html')
  
def list(request):
  rpc = loadRPC(request)
  
  files = rpc.poll()
  if not files:
    return HttpResponse("No filelist for user")
    
  output = '<ul>';
  dict = pickle.loads(b64decode(files.strip()))

  for path in dict:
    #path, key = f.split(':')
    key = dict[path]
    output += "<li><a href='/show?filename=%s'>%s</a></li>" % (path, path)
  return HttpResponse(output)
  #return HttpResponse(simplejson.dumps(files), mimetype='application/json')
  
def show(request):
  filename = request.GET.get('filename');
  if not filename:
    return HttpResponse("Didn't specify filename")
  rpc = loadRPC(request)
  
  output = ''
  files = rpc.poll()
  dict = pickle.loads(b64decode(files.strip()))
  
  for f in HttpResponse(dict.get(filename).get('files')):
    key = SHA.new(f).hexdigest()
    output += rpc.getData(key)
  return HttpResponse(output)
  

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

def md5_for_string(data, block_size=2**20):
  md5 = hashlib.md5()
  for i in xrange(0, len(data), block_size):
    md5.update(data[i:i+block_size])
  return md5.digest()