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
import sys, os
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_live import *
from bluetoothle.ble import *

class BleStreamLive(StreamLive):
    """Class for streaming live BLE data.
    
    Class for streaming live BLE data. Wrapper around a BleReader.
    
    Attributes:
        reader: BleReader.
    """
    # TODO(jake): remove name (there so can provide in stream_kitchen.py)
    def __init__(self, name=None, out_path=None, addrs=None, **kwargs):
        """Initialize live barcode stream."""
        StreamLive.__init__(self, out_path, **kwargs)
        self.reader = BleReader(addrs=addrs)
    
    def getCurrentData(self):
        """Get the current data.
        
        Get the current data returned from the reader's read() method."""        
        return self.reader.read()
