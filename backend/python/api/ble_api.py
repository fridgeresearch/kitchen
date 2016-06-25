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
import sys, os, argparse, json, urllib2, inspect, logging, tornado, threading, time, select
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from tornado import ioloop, web, websocket, gen
from kitchen import *
from utils.logging_utils import *

## Temp
import random

bles = {}

apps = []

def getDict(pathparts):
    d = pathparts[1].split('?')[1]
    d = str(urllib2.unquote(d))
    d = json.loads(d)
    return d

class BleServerWrapper:
    def __init__(self, port, debug=False):
        self.port = port
        handlers = [(r"/", MainHandler),
                (r"/ws", BleMasterWSHandler),
                (r"/led(On|Off|Pulse).*", LedHandler),
                (r"/wsapp", AppWSHandler),                
                (r"/weights.*", LedHandler)]
        self.app = tornado.web.Application(handlers,
                                           template_path=os.path.join(os.path.dirname(__file__), "ble_templates"),
                                           static_path=os.path.join(os.path.dirname(__file__), "ble_static"),
                                           debug=debug)
    def serveSync(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s port %s', func_name, self.port)
        self.app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()
        
    def serveAsync(self):
        func_name = inspect.stack()[0][3]
        logging.info('main starting tornado server at port %s', self.port)
        self.app.listen(self.port)
        threading.Thread(target=tornado.ioloop.IOLoop.instance().start).start()

    def listenForSignal(self):
        while True:
            r = select.select([sys.stdin], [], [], 0.1)[0]
            if r and sys.stdin.readline()[:-1]=='q': break

    def shutdown(self):
        logging.info('main stopping tornado server')
        tornado.ioloop.IOLoop.instance().stop()
        logging.info('main done')

class LedHandler(tornado.web.RequestHandler):
    def post(self, style=None):
        func_name = inspect.stack()[0][3]
        logging.info('%s style=%s', func_name, style)
        pathparts = self.request.uri.split('/')
        d = getDict(pathparts)
        logging.info('%s d=%s', func_name, d)
        if d == None: return None
        for addr in d['addrs']:
            if addr not in bles: continue
            msg = u'led %s %s' % (style.lower(), addr)
            if style.lower() != "off":
                msg = msg + ' %s %d' % (d['color'], d['duration'])
            logging.info('%s sending msg = %s', func_name, msg)
            if bles[addr]['wsh'] != None:
                bles[addr]['wsh'].write_message(msg)
        self.write('OK')
    
    def get(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s', func_name)
        pathparts = self.request.uri.split('/')
        d = getDict(pathparts)
        logging.info('%s d=%s', func_name, d)
        if d == None: return None
        addr_to_wt = {}
        for addr in d['addrs']:
            if addr in bles:
                if bles[addr]['wsh'] != None:
                    bles[addr]['wsh'].write_message(u'weight %s' % (addr))
                addr_to_wt[addr] = bles[addr]["weight"]
            else:
                addr_to_wt[addr] = None
        self.write(json.dumps(addr_to_wt))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class BleMasterWSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s websocket opened from %s', func_name, self.request.remote_ip)
        # Request the list of all devices currently visible to the BLE Master
        self.write_message(u"ls")
        logging.info('%s ls on %s', func_name, self.request.remote_ip)

    def on_message(self, message):
        func_name = inspect.stack()[0][3]
        logging.info('%s msg received from %s content %s', func_name, self.request.remote_ip, message)

        parts = message.split()
        bleaddr = parts[1]
        if bleaddr not in bles:
            bles[bleaddr] = {}
        bles[bleaddr]['remote_ip'] = self.request.remote_ip
        bles[bleaddr]['wsh'] = self

        if parts[0] == 'dev':            
            bles[bleaddr]['rssi'] = parts[2]
            bles[bleaddr]['weight'] = None
            logging.info('%s added device %s', func_name, bles[bleaddr])
        elif parts[0] == 'weight':
            logging.info('%s weight float to be converted %s', func_name, parts[2])
            bles[bleaddr]['weight'] = float(parts[2]) 
            if bles[bleaddr]['weight'] <= -30000.0:
                bles[bleaddr]['weight'] = None
            logging.info('%s update addr %s weight %s', func_name, bles[bleaddr], str(bles[bleaddr]['weight']))
        elif parts[0] == 'button_press':
            logging.info('%s button pressed %s', func_name, parts[2])
            try:
                button = int(parts[2])
                for a in apps:
                    msg = u"button %d" % (button - 1)
                    logging.info('%s SEND %s @%s' % (func_name, msg, a.request.remote_ip))
                    try:
                        a.write_message(msg)
                    except Exception as e:
                        pass
            except Exception as e:
            #except ValueError:
                logging.info('%s cannot convert button number from %s to int', func_name, parts[2])   
        elif parts[0] == 'ping':
            self.write_message(u"pong %f" % time.time())
            logging.info('%s send pong @%f', func_name, time.time())    

    def on_close(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s websocket closed for %s', func_name, self.request.remote_ip)
        # Remove all connection info for all BLE devices that were connected through this WebSocket
        for ble in bles:
            if bles[ble]['remote_ip'] == self.request.remote_ip:
                bles[ble]['remote_ip'] = None
                bles[ble]['wsh'] = None


class AppWSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s CONNECT @%s', func_name, self.request.remote_ip)
        logging.info(self.request)
        logging.info('%s SEND hello @%s', func_name, self.request.remote_ip)
        self.write_message(u"hello")
        apps.append(self)


    def on_message(self, message):
        func_name = inspect.stack()[0][3]
        logging.info('%s RCV %s @%s', func_name, message, self.request.remote_ip)

        if message == 'start':
            logging.info('%s start', func_name)
            #self.loopy()

        logging.debug('%s return', func_name)           


    def on_close(self):
        func_name = inspect.stack()[0][3]
        logging.info('%s CLOSE @%s', func_name, self.request.remote_ip)

    # @gen.coroutine
    # def loopy(self):
    #     func_name = inspect.stack()[0][3]
    #     logging.debug('%s enter', func_name)
    #     while True:
    #         msg = u"button %d" % random.randint(1,4)
    #         logging.info('%s SEND %s @%s' % (func_name, msg, self.request.remote_ip))
    #         # Pretend that a button was pressed
    #         self.write_message(msg)
    #         # Now sleep for 1-5 seconds
    #         yield gen.sleep(random.randint(1,5))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--data", help="Data.", default=DATA)
    parser.add_argument("--log", help="Log file.")
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--debug", help="Run in debug mode.", action='store_true')
    args = parser.parse_args()
    
    if not args.log: args.log = default=join(args.data, "ble.log")
    configureLogging(args.log)
    config = json.loads(open(args.service_config).read())
    
    s = BleServerWrapper(config["ble-api-port"], debug=args.debug)
    s.serveSync()
    #s.listenForSignal()
    #s.shutdown()
