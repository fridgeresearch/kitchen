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
import struct, binascii

WS_CONNECT_TIMEOUT = 10

SCAN_INTERVAL = 600

connections = {}

ble_devices = {}

client = None


class BleMasterServerWrapper:
    def __init__(self, server, port, device_name):
        self.server = server
        self.port = port
        self.device_name = device_name

    def serveSync(self):
        logging.info('main starting ble_master')
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.run_sync(lambda: main(self.server, self.port, self.device_name))
 
@gen.coroutine
def readButtons(device, wsclient):
    func_name = inspect.stack()[0][3]
    
    yield connect_dev(device.addr)
    
    while True:
        bits = connections[device.addr].readCharacteristic(14)
        logging.debug('%s read %s from device %s', func_name, binascii.hexlify(bits), device.addr)
        if len(bits) == 4:
            (button, ) = struct.unpack('<i', bits)
            if button >= 2 and button <= 6:
                send_msg = 'button_press %s %s' % (device.addr, button)
                logging.info('%s local msg=%s', func_name, send_msg)
                wsclient.write_message(send_msg)
                send_data(device.addr, 'ack')
        yield gen.sleep(1)

#@gen.coroutine
#def device_type(dev):
#    for (adtype, desc, value) in dev.getScanData():
#        if adtype == 9 and desc == config['ble-device-name']:
#            raise gen.Return(config['ble-device-name'])
#    raise gen.Return(None)


clients = {}

class WsConn:
    def __init__(self, server, timeout):
        func_name = inspect.stack()[0][3]
        self.connection = None
        self.alive = 0
        self.ping_time = 0
        self.pong_time = 0
        self.server = server
        self.timeout = timeout
        self.bles = None
        logging.debug('%s WsConn created', func_name)

    def setBle(self, bles):
        self.bles = bles

    @gen.coroutine
    def connect(self):
        func_name = inspect.stack()[0][3]
        logging.debug('%s called', func_name)
        if self.connection == None:
            try:
                logging.debug('%s Trying to connect to %s', func_name, self.server)
                self.connection = yield tornado.websocket.websocket_connect(self.server, connect_timeout=self.timeout, on_message_callback=self.read)
                self.alive = 1
            except:
                logging.debug('%s Connection to %s FAILED', func_name, self.server)
                self.connection = None
                self.alive = 0
        logging.debug('%s done alive=%d', func_name, self.alive)
   
    @gen.coroutine
    def isAlive(self):
        func_name = inspect.stack()[0][3]
        logging.debug('%s called', func_name)

        if not self.connection:
            self.alive = 0
            logging.debug('%s not alive return=%s', func_name, self.alive)
        else:
            if (self.pong_time - self.ping_time) > self.timeout:
                self.alive = 0
                self.connection = None
                logging.debug('%s server timeout @%f', func_name, time.time())
            else:
                self.ping_time = time.time()
                yield self.connection.write_message('ping %f' % self.ping_time)
                logging.debug('%s sent ping @%f',  func_name, self.ping_time)

    @gen.coroutine
    def periodic(self):
        yield self.connect()
        yield self.isAlive()

    @gen.coroutine
    def sendDev(self, msg):
        yield self.connection.write_message(msg)

    @gen.coroutine
    def read(self, msg):
        func_name = inspect.stack()[0][3]

        logging.debug('%s received msg=%s', func_name, msg)
        if msg is None:
            self.connection.close()
            self.alive = 0
            self.connection = None
            self.ping_time = 0
            self.pong_time = 0
        elif len(msg) > 6 and msg.startswith('pong '):
            self.alive = 1
            self.pong_time = time.time()
            logging.debug('%s pong @%f', func_name, self.pong_time)
        elif msg == 'ls':
            logging.debug('%s ls devices', func_name)
            if not self.bles: return
            dev_list = yield self.bles.device_list()
            logging.debug('%s ble list=%s', func_name, dev_list)
            for d in dev_list:
                logging.debug('%s send device=%s', func_name, d)
                self.connection.write_message(d)
        elif len(msg) > 7 and msg.startswith('led on '):
            # led on ab:ba:de:ad:ab:ba bb00bb 3000
            msg_parts = msg.split()
            if len(msg_parts) != 5:
                logging.error('%s malformed led on message len=%d expected len=5', func_name, len(msg_parts))
            yield self.bles.LedOn(msg_parts[2], msg_parts[3], int(msg_parts[4]))

class BleDevs:
    def __init__(self, scan=10, supported=['Frankenware']):
        func_name = inspect.stack()[0][3]
        self.devices = {}
        self.cons = {}
        self.scan_last = 0
        self.scan_interval = scan
        self.supported_devs = supported
        self.ws = None
        logging.debug('%s BleDevs created', func_name)

    def setWs(self, ws):
        self.ws = ws

    def scan_devs(self):
        func_name = inspect.stack()[0][3]
	logging.debug('%s start BLE scan', func_name)
        adapter = Scanner(0)
        devices = adapter.scan(10.0)
        logging.debug('%s found %d devices', func_name, len(devices))
        for d in devices:
            logging.debug('%s inspecting device %s', func_name, d.addr)
            for (tag, desc, value) in d.getScanData():
                logging.debug('%s tag=%s desc=%s value=%s',
                    func_name, tag, desc, value)
                if tag == 9 and value in self.supported_devs:
                    logging.debug('%s compatible device @%s', func_name, d.addr)
                    if d.addr not in self.devices:
                        self.devices[d.addr] = d
                        logging.info('%s added device @%s to ble_devices', 
                            func_name, d.addr)
                        self.cons[d.addr] = Peripheral(d.addr, 'random')
                        self.sendDevice(d.addr)
                        logging.info('%s connected to device @%s', func_name, d.addr)
        logging.debug('%s devices=%s', func_name, self.devices)
        logging.debug('%s cons=%s', func_name, self.cons)
        logging.debug('%s done BLE scan', func_name)

    @gen.coroutine
    def device_list(self):
        dev_list = []
        for d in self.devices:
            if self.devices[d].scanData[9] == 'FrankenwareBut':
                dev_list.append('buttons %s' % d)
            elif self.devices[d].scanData[9] == 'FrankenwareLED':
                dev_list.append('leds %s' % d)
            elif self.devices[d].scanData[9] == 'Frankenware':
                dev_list.append('dev %s' % d)
        logging.debug('dev list in BleDevs=%s', dev_list)
        raise gen.Return(dev_list)
   
    def sendDevice(self, addr):
        if not self.ws:
            return
        if self.devices[addr].scanData[9] == 'FrankenwareBut':
            self.ws.sendDev('buttons %s' % addr)
        elif self.devices[addr].scanData[9] == 'FrankenwareLED':
            self.ws.sendDev('leds %s' % addr)
        elif self.devices[addr].scanData[9] == 'Frankenware':
            self.ws.sendDev('dev %s' % addr)

    @gen.coroutine
    def scan(self):
        func_name = inspect.stack()[0][3]
        logging.debug('%s current=%f last=%f interval=%f', func_name, time.time(), self.scan_last, self.scan_interval)
        if (time.time() - self.scan_last) > self.scan_interval:
            logging.info('%s re-scan for BLE devices', func_name)
            self.scan_last = time.time()
            self.scan_devs()
            

    @gen.coroutine
    def read(self):
        #for d in self.cons:
        pass

    @gen.coroutine
    def LedOn(self, addr, color, duration):
        func_name = inspect.stack()[0][3]
        logging.debug('%s addr=%s color=%s duration=%d', func_name, addr, color, duration)
        if addr not in self.cons:
            if addr not in self.devices:
                logging.error('%s device @%s not available', func_name, addr)
                return
            self.cons[addr] = Peripheral(addr, 'random') # should have been connected already
            logging.info('%s connected to device @%s', func_name, addr)
        logging.debug(repr(color))
        logging.debug(repr(struct.pack('<L', duration)))
        msg = 'on ' + color.encode('ascii', 'strict') + struct.pack('<L', duration)
        yield self.cons[addr].writeCharacteristic(17, msg)

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
        raise gen.Return(-30000.0);
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

              


@gen.coroutine
def main():
#server, port, device_name):
    func_name = inspect.stack()[0][3]
    SERVER = 'ws://%s:%d/ws' % (config['ble-api-server'], config['ble-api-port'])

    # in seconds
    BLE_SCAN_INTERVAL = 300
    #clients[SERVER] = yield

    #client = yield tornado.websocket.websocket_connect(SERVER, connect_timeout=WS_CONNECT_TIMEOUT)
    #ws_connect(SERVER, WS_CONNECT_TIMEOUT)
    #logging.info('%s connected to %s', func_name, SERVER)

    #connection = yield ws_connect(SERVER, WS_CONNECT_TIMEOUT)
    #connection = yield tornado.websocket.websocket_connect(SERVER)
    devices = {}
    last_devices_scan = 0


    #print type(connection)
    wc = WsConn(SERVER, WS_CONNECT_TIMEOUT)
    bles = BleDevs(scan=BLE_SCAN_INTERVAL, supported=['FrankenwareBut', 'FrankenwareLED'])

    bles.scan()

    bles.setWs(wc)
    wc.setBle(bles)


    io_loop = tornado.ioloop.IOLoop.current()

    tornado.ioloop.PeriodicCallback(bles.scan, BLE_SCAN_INTERVAL * 1000, io_loop=io_loop).start()
    tornado.ioloop.PeriodicCallback(wc.periodic, WS_CONNECT_TIMEOUT * 1000, io_loop=io_loop).start()
    #tornado.ioloop.PeriodicCallback(wc.isAlive, WS_CONNECT_TIMEOUT * 500).start()
    #yield wc.connect(SERVER, WS_CONNECT_TIMEOUT)
    #yield bles.scan()
    #yield wc.isAlive()
   
    #tornado.ioloop.IOLoop.make_current() #current().start()
    #io_loop = tornado.ioloop.IOLoop.current()
    #io_loop.start()
    #io_loop.run_sync()

    #io_loop = tornado.ioloop.IOLoop.current()
    io_loop.start()



 
#    while True:
#        lives = yield wc.isAlive()
#        if lives == 0:
#            logging.debug('%s Not alive we should connect...', func_name)
#            yield wc.connect(SERVER, WS_CONNECT_TIMEOUT)
#        yield bles.scan()
#        yield wc.read(bles)
        
        
#        print devices



"""
    while True:
        yield scan_devs(devices, ['FrankenwareBut', 'FrankenwareLED'])

        msg = yield connection.read_message()
        msg = None
        logging.info('%s remote msg=%s', func_name, msg)
        if msg is None:
            client.close()
            logging.info('%s remote closed connection', func_name)
            logging.info('%s reconnect in 10s', func_name)
            conections = {}
            time.sleep(10)
            client = yield tornado.websocket.websocket_connect(SERVER)
            logging.info('%s connected to %s', func_name, SERVER)
        elif msg == 'ls':
            devices = yield scan_devs(device_name)
            for d in devices:
                yield connect_dev(d.addr)
                send_msg = ''
                if d.scanData[9] == 'FrankenwareBut':
                    send_msg = 'buttons %s %s %s' % (d.addr, d.rssi, d.connectable)
                    yield readButtons(d, client)
                elif d.scanData[9] == 'Frankenware':
                    send_msg = 'dev %s %s %s' % (d.addr, d.rssi, d.connectable)
                logging.info('%s local msg=%s', func_name, send_msg)
                client.write_message(send_msg)
        elif msg[0:8] == 'connect ':
                addr = msg.split()[1]
                yield connect_dev(addr)
        # led on ab:ba:de:ad:ab:ba bb00bb 3000
        elif msg[0:7] == 'led on ':
            msg_parts = msg.split()
            addr = msg_parts[2]
            send_msg = 'on %s %s' % (msg_parts[3], msg_parts[4])
            yield send_data(addr, send_msg)
        # led off ab:ba:de:ad:ab:ba
        elif msg[0:8] == 'led off ':
            msg_parts = msg.split()
            addr = msg_parts[2]
            send_msg = 'off'
            yield send_data(addr, send_msg)
        # led pulse ab:ba:de:ad:ab:ba bb00bb 3000
        elif msg[0:10] == 'led pulse ':
            msg_parts = msg.split()
            addr = msg_parts[2]
            send_msg = 'pulse %s %s' % (msg_parts[3], msg_parts[4])
            yield send_data(addr, send_msg)
        elif msg[0:7] == 'weight ':
            addr = msg.split()[1]
            send_msg = 'weight'
            yield send_data(addr, send_msg)
            #yield connect_dev(addr)
            #connections[addr].writeCharacteristic(17, 'weight', withResponse=True)

            rdata = yield read_data(addr)
            return_msg = 'weight %s %f' % (addr, rdata)
            logging.info('%s local msg=%s', func_name, return_msg)
            client.write_message(return_msg)
"""
 

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

    #s = BleMasterServerWrapper(config['ble-api-server'], config['ble-api-port'], \
    #                           config['ble-device-name'])
    #s.serveSync()
    
    #io_loop = tornado.ioloop.IOLoop.current()
    #io_loop.run_sync(main)
    main()

    logging.info('main ble_master done')
