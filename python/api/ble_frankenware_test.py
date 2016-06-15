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
from bluepy.btle import Scanner, Peripheral
import struct

connections = {}

@gen.coroutine
def scan_devs(ble_device_name):
    func_name = inspect.stack()[0][3]
    adapter = Scanner(0)
    devices = adapter.scan(10.0)
    logging.info('%s found devices=%s', func_name, devices)
    our_devices = []
    for d in devices:
        logging.info('%s inspecting device %s @%s', func_name, d, d.addr)
        #if d.addr[0:8] != 'f8:6a:a4': continue
        logging.info('%s run getScanData for %s', func_name, d)
        for (tag, desc, value) in d.getScanData():
            logging.info('%s tag=%s desc=%s value=%s config-value=%s',
                         func_name, tag, desc, value, ble_device_name)
            if tag == 9 and value == ble_device_name:
                logging.info('%s frankenware @%s', func_name, d.addr)
                our_devices.append(d)
        logging.info('%s done scanning', func_name)
    raise gen.Return(our_devices)

@gen.coroutine
def connect_dev(addr):
    func_name = inspect.stack()[0][3]
    if addr not in connections:
        connections[addr] = Peripheral(addr, 'random')
        logging.info('%s connected to %s', func_name, addr)

@gen.coroutine
def read_data(addr):
    func_name = inspect.stack()[0][3]
    weight_bytes = connections[addr].readCharacteristic(14)
    if len (weight_bytes) != 4: 
        logging.info('%s read invalid data from %s', func_name, addr)
        raise gen.Return(500.0);
    (weight, ) = struct.unpack('<f', weight_bytes)
    logging.info('%s weight=%f', func_name, weight)
    raise gen.Return(weight)

# Send data to the device
@gen.coroutine
def send_data(addr, msg):
    func_name = inspect.stack()[0][3]
    yield connect_dev(addr)
    connections[addr].writeCharacteristic(17, msg)
    logging.info('%s sent addr=%s local msg=%s', func_name, addr, msg)

class BleMasterServerWrapper:
    def __init__(self, server, port, device_name):
        self.server = server
        self.port = port
        self.device_name = device_name

    def serveSync(self):
        logging.info('main starting ble_master')
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.run_sync(lambda: main(self.server, self.port, self.device_name))

#@gen.coroutine
#def device_type(dev):
#    for (adtype, desc, value) in dev.getScanData():
#        if adtype == 9 and desc == config['ble-device-name']:
#            raise gen.Return(config['ble-device-name'])
#    raise gen.Return(None)

@gen.coroutine
def led_on(addrs, color, duration):
    func_name = inspect.stack()[0][3]
    for addr in addrs:
        send_msg = 'on %s %s' % (color, duration)
        logging.info('%s sending %s @%s', func_name, send_msg, addr)
        yield send_data(addr, send_msg)

@gen.coroutine
def led_pulse(addrs, color, duration):
    func_name = inspect.stack()[0][3]
    for addr in addrs:
        send_msg = 'pulse %s %s' % (color, duration)
        logging.info('%s sending %s @%s', func_name, send_msg, addr)
        yield send_data(addr, send_msg)

@gen.coroutine
def led_off(addrs):
    func_name = inspect.stack()[0][3]
    for addr in addrs:
        send_msg = 'off'
        logging.info('%s sending %s @%s', func_name, send_msg, addr)
        yield send_data(addr, send_msg)

@gen.coroutine
def weight(addrs):
    func_name = inspect.stack()[0][3]
    for addr in addrs:
        send_msg = 'weight' 
        logging.info('%s sending %s @%s', func_name, send_msg, addr)
        yield send_data(addr, send_msg)
        rdata = yield read_data(addr)
        logging.info('%s weight %s @%s', func_name, rdata, addr)

@gen.coroutine
def main(server, port, device_name):
    func_name = inspect.stack()[0][3]
    SERVER = 'ws://%s:%d/ws' % (server, port)
    DEVS = [''] # FILL IN

    for addr in DEVS:
        yield connect_dev(addr)

    yield led_on(DEVS, 'aaaa00', '3000')
    time.sleep(4)
    yield weight(DEVS)
    yield led_pulse(DEVS, '00aaaaa', '3000')
    time.sleep(4)
    yield weight(DEVS)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--data", help="Data.", default=DATA)
    parser.add_argument("--log", help="Log file.")
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--debug", help="Run in debug mode.", action='store_true')
    args = parser.parse_args()
    
    if not args.log: args.log = default=join(args.data, "ble_master.log")
    configureLogging(args.log)
    config = json.loads(open(args.service_config).read())

    s = BleMasterServerWrapper(config['ble-api-server'], config['ble-api-port'], \
                               config['ble-device-name'])
    s.serveSync()
    
    #io_loop = tornado.ioloop.IOLoop.current()
    #io_loop.run_sync(main)

    logging.info('main ble_master done')
