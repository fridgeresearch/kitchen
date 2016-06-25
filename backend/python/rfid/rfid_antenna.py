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
import sys, os, subprocess, datetime, threading, Queue
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from rfid.rfid_tag_read import *
from rfid.rfid_reader_async import *

class RfidAntenna():
    """Class for reading RFID data from an antenna.
    
    Class for reading RFID data from an antenna. RFID Reader dictionary
    shared amongst all antenna readers.

    Attributes:
        readers: Dictionary from interface to reader (class variable).
        readers_lock: Lock ensures atomic access to readers (class variable).
        interface: Input interface (eth or usb).
        antenna: Antenna name.
    """
    readers = {}
    readers_lock = threading.Lock()
    def __init__(self, interface, antenna, power=None, session=None, **kwargs):
        self.interface, self.antenna = interface, antenna
        if interface=="eth" and session==None: session="S0" # TODO: don't hard code
        if interface not in RfidAntenna.readers:
            with RfidAntenna.readers_lock:
                RfidAntenna.readers[interface] = RfidReaderAsync(interface, power=power, session=session)

    def release(self):
        if self.interface in RfidAntenna.readers:
            with RfidAntenna.readers_lock:
                RfidAntenna.readers[self.interface].release()
                del RfidAntenna.readers[self.interface]

    def read(self):
        with RfidAntenna.readers_lock:
            return RfidAntenna.readers[self.interface].read(antennas=[self.antenna])
