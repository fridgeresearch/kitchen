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
import sys, os, argparse, json, urllib2, inspect, logging, tornado, time
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from tornado import ioloop, web, websocket, gen
from kitchen import *
from utils.logging_utils import *
# from bluepy.btle import Scanner, Peripheral
import struct

@gen.coroutine
def main():
    func_name = inspect.stack()[0][3]
    SERVER = 'ws://%s:%d/wsapp' % (config['ble-api-server'], config['ble-api-port'])

    client = yield tornado.websocket.websocket_connect(SERVER)
    logging.info('%s CONNECT @%s', func_name, SERVER)
    #logging.info(client)
    while True:
        msg = yield client.read_message()
        logging.info('%s RCV %s @%s', func_name, msg, SERVER)
        if msg is None:
            client.close()
            logging.info('%s CLOSED @%s', func_name, SERVER)
            sys.exit(0)
        elif msg == 'hello':
            client.write_message('start')
            logging.info('%s SEND %s @%s', func_name, 'start', SERVER)
        elif msg[0:7] == 'button ':
            button = int(msg.split()[1])
            logging.info('BUTTON=%d', button)
 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--data", help="Data.", default=DATA)
    parser.add_argument("--log", help="Log file.")
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--debug", help="Run in debug mode.", action='store_true')
    args = parser.parse_args()
    
    if not args.log: args.log = default=join(args.data, "ws_app.log")
    configureLogging(args.log)
    config = json.loads(open(args.service_config).read())

    logging.info('main starting ws_app')

    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(main)

    logging.info('main ws_app done')
