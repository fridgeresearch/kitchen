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
from kitchen import *
from rfid.rfid_tag_read import *
from data_stream.stream_recorded import *

class RfidAntennaStreamRecorded(StreamRecorded):
    """Class for streaming recorded RFID antenna data."""
    def __init__(self, in_dir):
        """Initialize the stream.
        
        Args:
            in_dir: Input directory."""
        StreamRecorded.__init__(self, in_dir)
        self.updateCurrent()

    def init(self, s_idx):
        """Initialize the times and data for the specified segment.
        
        Reads times and data from times.txt and data.txt, respectively.
        
        Args:
            s_idx: Segment index to initialize."""
        StreamRecorded.init(self, s_idx)
        data_fname  = join(self.in_dir, self.seg_names[s_idx], "data.txt")
        # Read list of RfidTagRead objects from the data file 
        # (since dumped by casting to string).
        self.data[s_idx] = [[RfidTagRead(*v.strip().split())] for v in open(data_fname)]
