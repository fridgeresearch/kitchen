"""
The MIT License (MIT)

Copyright (c) 2016 Jake Lussier (Stanford University)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
"""
TODO: License info

App server.
"""

import sys, os, json, inspect, threading, urllib2, logging, select
from os.path import *
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

class ServerWrapper:
  """Class wrapping ThreadedHttpServer so can easily pass args."""
  def __init__(self, host, port, handlerInit):
    func_name = inspect.stack()[0][3]
    logging.info('%s', func_name)
    self.server = ThreadedHTTPServer((host, port), handlerInit)
  def serveSync(self):
    func_name = inspect.stack()[0][3]
    logging.info('%s', func_name)
    self.server.serve_forever()
  def serveAsync(self):
    func_name = inspect.stack()[0][3]
    logging.info('%s', func_name)
    self.serve_thread = threading.Thread(target=self.server.serve_forever)
    self.serve_thread.daemon = True    
    self.serve_thread.start()
  def listenForSignal(self):
    logging.info("Enter 'q' to shutdown server...")
    while True:
      r = select.select([sys.stdin], [], [], 0.1)[0]
      if r and sys.stdin.readline()[:-1]=='q': break
  def shutdown(self):
    func_name = inspect.stack()[0][3]
    logging.info('%s Joining serve thread.', func_name)
    self.server.shutdown()
    self.serve_thread.join()
    logging.debug('%s DONE.', func_name)

class Handler(BaseHTTPRequestHandler):
  """Processes HTTP requests. 

  Functions do_HTTP_METHOD_NAME are implicitly used to process different HTTP
  methods requested.
  
  Class attributes:
      err_codes: Dictionary of error codes.
  """
  err_codes = json.loads(open(HTTP_RESPONSES_CONFIG).read())
  def __init__(self, *args):
    """Constructor."""
    if args != ():
      BaseHTTPRequestHandler.__init__(self, *args)
  
  def _extractDict(self, pathparts, keys, name, func_name):
    """
    if '?' not in pathparts[1]:
      self.sendError(400, message="%s requires arguments."%name, caller=func_name)
      return None
    """
    try:
      data = pathparts[1].split('?')[1]
      data = str(urllib2.unquote(data))
      data = json.loads(data)
    except Exception as e:
      self.sendError(400, message="Invalid json=%s."%str(data), caller=func_name)
      return None
    if keys != None and sorted(data.keys()) != sorted(keys):
      err_msg = "%s arguments must be %s." % (name, ', '.join(keys))
      self.sendError(400, message=err_msg, caller=func_name)
      return None
    return data

  def _sendHelper(self, response, message="", text="plain", extra=[]):
    """Send helper."""
    self.send_response(response, message)
    for (k, v) in extra: self.send_header(k, v)
    self.send_header('Content-type', 'text/%s'%text)
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Credentials', 'true')
    self.end_headers()

  def sendError(self, err_code, message="", caller=""):
    """Sends error code and (optionally) message."""
    if str(err_code) in Handler.err_codes:
      err_name = Handler.err_codes[str(err_code)]
    else:
      k = ("%03d"%err_code)[0] + "??"
      err_name = Handler.err_codes[k] if k in Handler.err_codes else "Unknown"
    logging.error("%s %d:%s", caller, err_code, message)
    self._sendHelper(err_code, message=message, text="plain")
    self.wfile.write('%d/%s\n\n%s' % (err_code, err_name, message))

  def sendData(self, data):
    self._sendHelper(200, text="json")
    if data != None:
      self.wfile.write(json.dumps(data))

  def do_OPTIONS(self):
    """Needed for proper processing of AJAX requests. Modern browsers will
    issue an OPTIONS request first and only after that issue a full request.
    """
    self.send_response(200, "ok")
    self.send_header('Access-Control-Allow-Methods', 'DELETE, GET, HEAD, OPTIONS, POST')
    self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
    self.send_header("Access-Control-Allow-Headers", "Content-Type")
    self.send_header("Access-Control-Allow-Headers", "Authorization")
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Credentials', 'true')    
    self.end_headers()

  def do_AUTHHEAD(self):
    """Sends out the headers for un-authenticated connections. 

    Not really important right now as we are not using authentication but 
    eventually we should check usernames and passwords.
    """
    func_name = inspect.stack()[0][3]
    logging.info('%s Sending auth needed header', func_name)
    extra = [('WWW-Authenticate', 'Basic realm=\"ServerKitchen\"')]
    self._sendHelper(401, text="html", extra=extra)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
