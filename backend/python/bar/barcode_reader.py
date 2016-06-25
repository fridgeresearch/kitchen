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
import sys, os, usb, datetime
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from bar.barcode_utils import *
from utils.general_utils import *

class BarcodeReader():
    """Class for reading barcode data over USB.
    """
    def __init__(self, vendor_id=0x13ba, product_id=0x0018, chunk_size=8, reset=True):
        """Initialize BarcodeReader to read data over USB.
        
        Args:
            vendor_id: Vendor ID.
            product_id: Product ID.
            chunk_size: Chunk size.
            reset: Reset.
        """
        self.interface, self.chunk_size, self.reset = 0, chunk_size, reset
        self._device = usb.core.find(idVendor=vendor_id, idProduct=product_id)        
        if self._device is None:
            raise Exception('No device found. vendor_id=%s, product_id%s' % (vendor_id, product_id))
        if self._device.is_kernel_driver_active(self.interface):
            try:
                self._device.detach_kernel_driver(self.interface)
            except usb.core.USBError as e:
                raise Exception('Could not detach kernel driver: %s' % str(e))
        try:
            self._device.set_configuration()
            if reset: self._device.reset()
        except Exception as e:
            raise Exception('Could not set configuration: %s' % str(e))
        self._endpoint = self._device[0][(0, 0)][0]

    def read(self, timeout=None):
        """Reads barcode data over USB
        
        Args:
            timeout: timeout (in seconds).
        
        Returns:
            A single Barcode() object or None.
        """
        data, data_str = [], ""
        while True:
            try:
                data += self._endpoint.read(self._endpoint.wMaxPacketSize, timeout=timeout)
                data_str = self._decode(data)
                if "\n" in data_str: break
            except usb.core.USBError as e:
                if e.args[1] == "Operation timed out": break
                else: raise Exception('Error: %s' % e.args[1])
        code, t = data_str.strip(), datetime.datetime.utcnow()
        return Barcode(dateTimeToTimeString(t), code) if code else None

    def _decode(self, data):
        return ''.join([shift_keys[data[v+2]] if data[v] else keys[data[v+2]] \
                        for v in xrange(0, len(data), self.chunk_size)])

    def disconnect(self):
        if self.reset: self._device.reset()
        usb.util.release_interface(self._device, self.interface)
        self._device.attach_kernel_driver(self.interface)

keys = [
    '', '', '', '',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '\n', '^]', '^H',
    '^I', ' ', '-', '=', '[', ']', '\\', '>', ';', "'", '`', ',', '.',
    '/', 'CapsLock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    'PS', 'SL', 'Pause', 'Ins', 'Home', 'PU', '^D', 'End', 'PD', '->', '<-', '-v', '-^', 'NL',
    'KP/', 'KP*', 'KP-', 'KP+', 'KPE', 'KP1', 'KP2', 'KP3', 'KP4', 'KP5', 'KP6', 'KP7', 'KP8',
    'KP9', 'KP0', '\\', 'App', 'Pow', 'KP=', 'F13', 'F14'
]

shift_keys = [
    '', '', '', '',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '\n', '^]', '^H',
    '^I', ' ', '_', '+', '{', '}', '|', '<', ':', '"', '~', '<', '>',
    '?', 'CapsLock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    'PS', 'SL', 'Pause', 'Ins', 'Home', 'PU', '^D', 'End', 'PD', '->', '<-', '-v', '-^', 'NL',
    'KP/', 'KP*', 'KP-', 'KP+', 'KPE', 'KP1', 'KP2', 'KP3', 'KP4', 'KP5', 'KP6', 'KP7', 'KP8',
    'KP9', 'KP0', '|', 'App', 'Pow', 'KP=', 'F13', 'F14'
]
