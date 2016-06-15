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
import sys, os, cv2, platform, numpy as np
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from data_stream.stream_recorded import *

class CameraStreamRecorded(StreamRecorded):
    """Class for streaming recorded camera data.
    
    Class for streaming recorded camera data. Streams wave data from disk.
    """
    def __init__(self, in_dir):
        """Initialize the stream.
        
        Args:
            in_dir: Input directory.
        """
        StreamRecorded.__init__(self, in_dir)
        self.caps = [None]*len(self.times)
        self.updateCurrent()

    def init(self, s_idx):
        """Initialize the times and data for the specified segment.
        
        Reads time from times.txt. VideoCapture object initialize from vid.avi.
        
        Args:
            s_idx: Segment index to initialize."""
        StreamRecorded.init(self, s_idx)
        vid_fname  = join(self.in_dir, self.seg_names[s_idx], "vid.avi")
        self.data[s_idx] = [None]*len(self.times[s_idx])
        self.caps[s_idx] = cv2.VideoCapture(vid_fname)

    def uninit(self, s_idx):
        """Unitinialize the specified segment.
        
        Args:
            s_idx: Segment index to uninitialize."""
        self.time_strs[s_idx], self.times[s_idx], \
            self.data[s_idx], self.caps[s_idx] = [None]*4

    def uninitAll(self):
        """Unitinialize the all segments."""
        [self.uninit(v) for v in range(self.numSegments())]
    
    def getData(self, s_idx, d_idx):
        """Get data for the given segment and data indices.
        
        Returns image for the given segment and data indices.
        Note that since we internally access the data using a VideoCapture
        object, we must read multiple times for frames in the near future
        and seek to far-off frames.
        
        Args:
           s_idx: Segment index.
           d_idx: Data index.
        
        Returns:
           Data.
        """
        if self.times[s_idx]==None: self.init(s_idx)
        if self.data[s_idx][d_idx] == None:
            # Get the next position to be read. If it is far-off,
            # seek to that exact position (by setting the CAP_PROP_POS_FRAMES
            # property). Otherwise use the read() method to read frames.
            next_pos = int(self.caps[s_idx].get(cv2.CAP_PROP_POS_FRAMES))
            if d_idx < next_pos or d_idx-next_pos > 20:
                self.caps[s_idx].set(cv2.CAP_PROP_POS_FRAMES, d_idx)
                next_pos = d_idx
            for j in range(next_pos, d_idx+1):
                (ret, im) = self.caps[s_idx].read()
            return im
        else:
            return self.data[s_idx][d_idx]
    
