# run this by doing .\ipy.exe compile.py

import sys
import clr

import os, fnmatch
import pyc

matches = []
for root, dirnames, filenames in os.walk('Lib'):
  for filename in fnmatch.filter(filenames, '*.py'):
    matches.append(os.path.join(root, filename))
    
for root, dirnames, filenames in os.walk('../server'):
  for filename in fnmatch.filter(filenames, '*.py'):
    #if "server.py" not in filename.lower():
    matches.append(os.path.join(root, filename))

gb = ["/out:PandoraServer", "/main:../server/Server.py", "/target:exe", "/platform:x86", "/embed"]

pyc.Main(matches + gb)
# ipy pyc.py /out:PandoraServer /main:server.py /target:exe