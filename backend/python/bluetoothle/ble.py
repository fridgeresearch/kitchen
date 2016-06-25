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
"""
import sys, os, struct, ctypes, ctypes.util, socket, Queue, threading
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from rfid.rfid_tag_read import *
from utils.general_utils import *

def encode(x):
    if type(x) == str: # python2.x
        return x.encode('hex')
    elif type(x) == int: # python3.x
        return "{0:02x}".format(x)
    else:
        raise Exception("cannot encode data of type %s" % str(type(x)))

def hexToSignedChar(h):
    x = int(h, 16)
    # if > 127, subtract off 256 (because negative)
    if x > 0x7F: x -= 0x100
    return x

class BleBeaconRead():
    """Class for storing BLE Beacon read data.
    
    Attributes:
       time_str: acquisition time string
       time: acquisition time.
       addr: Beacon address.
       rssi: Beacon RSSI.
    """
    def __init__(self, time_str, addr, rssi):
        """Initialize read with data."""
        self.time_str, self.time = time_str, timeStringToDateTime(time_str)
        self.addr, self.rssi = addr, int(rssi)
    def __str__(self):
        return "%s %s %d" % (self.time_str, self.addr, self.rssi)

class BleReader():
    """Class for reading BLE Beacons.
    
    Attributes:
       addrs: device addresses to listen for if None if want all.
       max_time: max_time to store tag before discarding.
       data:  Beacon read list.
       listen_thread: Thread that listens to the Java program.
    """
    def __init__(self, addrs=None, max_time=1.0):
        self.addrs = addrs
        self.max_time = max_time
        self.data = Queue.Queue()
        self.listen_thread = threading.Thread(target=self._listen)
        self.listen_thread.daemon = True; self.listen_thread.start()

    def release(self):
        self.listen_thread.join()
    
    def _listen(self):
        # Setup BLE reading.
        if not os.geteuid() == 0:
            raise Exception("BLE reading requires sudo.")
        btlib = ctypes.util.find_library("bluetooth")
        if not btlib:
            raise Exception("Can't find required bluetooth libraries (install bluez)")
        bluez = ctypes.CDLL(btlib, use_errno=True)
        dev_id = bluez.hci_get_route(None)
        hci_filter = struct.pack("<IQH", 0x00000010, 0x4000000000000000, 0) # allows LE advertising events
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI)
        sock.bind((dev_id,))
        sock.setsockopt(socket.SOL_HCI, socket.HCI_FILTER, hci_filter)
        err = bluez.hci_le_set_scan_parameters(sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000);
        if err < 0 and ctypes.get_errno() != 5:
            raise Exception("Set scan parameters failed")
        elif err >= 0:
            err = bluez.hci_le_set_scan_enable(sock.fileno(), 1, 0, 1000)
            if err < 0:
                raise Exception("Set scan enable failed")
        # Loop to read.
        while True:
                data = sock.recv(1024)
                addr = ':'.join([encode(x) for x in data[12:6:-1]])
                rssi = hexToSignedChar(encode(data[-1]))
                t_str = dateTimeToTimeString(datetime.datetime.utcnow())
                if self.addrs==None or addr in self.addrs:
                    self.data.put(BleBeaconRead(t_str, addr, rssi))
                while not self.data.empty():
                    t = datetime.datetime.utcnow()
                    try:
                        td = (t-self.data.queue[0].time).total_seconds()
                        if td > self.max_time:
                            self.data.get()
                        else: break
                    except Exception as e:
                        # Queue might have been emptied between checking empty and accessing.
                        pass

    def read(self):
        beacon_reads = []
        while not self.data.empty():
            beacon_reads.append(self.data.get_nowait())
        return beacon_reads

class BeaconPresenceClassifier:
    """Class for classifying whether or not an Beacon is present."""
    def eval(self, data, stable_start, stable_end):
        score = 0.0
        for (time, rssi) in data:
            score += (time>stable_start and time<stable_end) and rssi >= -69
        return score

class BeaconArrivalClassifier:
    """Class for classifying whether or not an Beacon just arrived."""
    def eval(self, data, prev_stable_start, prev_stable_end, stable_start, stable_end):
        score = 0.0
        for (time, rssi) in data:
            score += (time>stable_start and time<stable_end) and rssi >= -69
            score -= (time>prev_stable_start and time<prev_stable_end) and rssi >= -69
        return score

class BeaconRemovalClassifier:
    """Class for classifying whether or not an Beacon just arrived."""
    def eval(self, data, prev_stable_start, prev_stable_end, stable_start, stable_end):
        score = 0.0
        for (time, rssi) in data:
            score -= (time>stable_start and time<stable_end) and rssi >= -69
            score += (time>prev_stable_start and time<prev_stable_end) and rssi >= -69
        return score
