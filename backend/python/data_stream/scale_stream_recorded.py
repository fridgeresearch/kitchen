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
from data_stream.stream_recorded import *
from data_stream.scale_stream import *
from data_stream.load_cell_stream_recorded import *

class ScaleStreamRecorded(StreamRecorded, ScaleStream):
    """Class for streaming recorded scale data.
    
    Class for streaming recorded scale data.
    
    Attributes:
        streams: load cell streams for this scale.
    """
    def __init__(self, in_dir, sn):
        """Initialize the stream.
        
        Args:
            in_dir: Input directory.
            sn: Serial number.
        """
        StreamRecorded.__init__(self, in_dir)
        ScaleStream.__init__(self, sn)
        self.load_cell_names = sorted([w for w in sorted(os.listdir(in_dir)) \
                                       if "LoadCellStream" in w and sn in w])
        if len(self.load_cell_names) != 3:
            raise Exception("No %s scale calibration in %s." % (sn, in_dir))
        self.streams = [LoadCellStreamRecorded(join(in_dir, v)) \
                        for v in self.load_cell_names]
        self.seg_names = self.streams[0].seg_names
        self.times, self.data = [[None for v in self.seg_names] for i in range(2)]
        
    def init(self, s_idx):
        """Initialize the times and data for the specified segment.
        
        Reads time from times.txt. Data is read by iterating through data
        for one load cell and getting the nearest data temporally for the others.
        
        Args:
            s_idx: Segment index to initialize.
        """
        self.data[s_idx] = []
        for i in range(self.streams[0].numSegmentData(s_idx)):
            t = self.streams[0].getTime(s_idx, i)
            self.data[s_idx].append([v.getDataAtTime(s_idx,t) for v in self.streams])
        self.times[s_idx] = self.streams[0].times[s_idx]

    def getForceVector(self, s_idx, d_idx, tare_readings, warn=True):
        """Gets the force vector given the tare readings and segment / data indices.
        
        Args:
            s_idx: Segment index.
            d_idx: Data index.
            tare_readings: Tare readings.
        
        Returns:
            4-dimensional force vector.
        """
        return self.cal.predict(self.getData(s_idx, d_idx)-np.array(tare_readings), warn=warn)

    def getForceVectorAtTime(self, s_idx, t, tare_readings, warn=True):
        """Gets the force vector given the tare readings and segment index and time.
        
        Args:
            s_idx: Segment index.
            t: Time.
            tare_readings: Tare readings.
        
        Returns:
            4-dimensional force vector.
        """
        return self.cal.predict(self.getDataAtTime(s_idx, t)-np.array(tare_readings), warn=warn)

    def getLoadCellForces(self, s_idx, d_idx, tare_readings=[0,0,0], warn=True):
        """Gets the forces given the tare readings and segment index and time.
        
        Args:
            s_idx: Segment index.
            d_idx: Data index.
            tare_readings: Tare readings.
        
        Returns:
            3-dimensional vector of forces.
        """
        d = np.array(self.getData(s_idx, d_idx))
        return self.cal.predictLoadCellForces(d-np.array(tare_readings), warn=warn)
