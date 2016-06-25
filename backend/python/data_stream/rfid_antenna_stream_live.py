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
from rfid.rfid_antenna import *

class RfidAntennaStreamLive(StreamLive):
    """Class for streaming live RFID data.
    
    Class for streaming live RFID data. Wrapper around an RfidAntenna.
    
    Attributes:
        reader: RfidAntenna.
    """    
    def __init__(self, name, out_path=None, **kwargs):
        """Initialize live RFID stream.
        
        Args:
            name: RFID antenna name of the form <interface><antenna>.
        """
        StreamLive.__init__(self, out_path, **kwargs)
        interface, antenna = name[:-1].lower(), name[-1]
        self.reader = RfidAntenna(interface, antenna, **kwargs)
        
    def getCurrentData(self):
        """Get the current data.
        
        Get the current data returned from the reader's read() method.
        """        
        return self.reader.read()

    def release(self):
        """Release the RFID antenna reader."""
        StreamLive.release(self)
        return self.reader.release()
