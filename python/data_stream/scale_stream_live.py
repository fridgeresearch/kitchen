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
import sys, os, numpy as np
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from utils.general_utils import *
from data_stream.stream_live import *
from data_stream.scale_stream import *
from data_stream.load_cell_stream_live import *
from scales.scale_calibration import *

class ScaleStreamLive(StreamLive, ScaleStream):
    """Class for streaming live scale data.
    
    Class for streaming live scale data. Contains LoadCellStreamLive list.
    
    Attributes:
        streams: LoadCellStreamLive list.
    """    
    def __init__(self, sn, out_path=None, **kwargs):
        """Initialize the LoadCellStreamLive list.
        
        Args:
            sn: Serial number.
            bridge_inputs: Bridge inputs.
        """
        StreamLive.__init__(self, out_path, **kwargs)
        ScaleStream.__init__(self, sn)
        self.streams = []
        for i in range(3):
            p = ("%s-%d"%(out_path.replace("Scale", "LoadCell"),i))\
                if out_path else None
            self.streams.append(LoadCellStreamLive("%s-%d"%(sn,i), p))
        
    def getCurrentData(self):
        """Get the current data.
        
        Get the current data returned from the LoadCellStreamLive list.
        """
        return [v.getCurrentData() for v in self.streams]

    def createWriter(self, start_time, time_buffer=0.0, **kwargs):
        [v.createWriter(start_time, time_buffer, **kwargs) for v in self.streams]

    def setWriterEndTimes(self, end_time):
        [v.setWriterEndTimes(end_time) for v in self.streams]

    def write(self, time, data):
        [s.write(time, d) for (s, d) in zip(self.streams, data)]

    def closeWriters(self, time):
        [v.closeWriters(time) for v in self.streams]
