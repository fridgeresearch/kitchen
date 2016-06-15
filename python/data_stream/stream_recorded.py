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
import sys, os, bisect, dateutil.parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from utils.general_utils import *

class StreamRecorded:
    """Abstract Class for streaming recorded data.
    
    Class for streaming recorded data. Note that provides same interface as StreamLive
    when accessing current data.
    
    Attributes:
        done: Whether or not we are done streaming.
        in_dir: Input directory from which we read.
        seg_names: Segment names.
        data: Data (list for each segment)
        times: Times (list of datetime objects for each segment)
        time_strs: Time strings (list of time strings for each segment)
        current_seg_idx: Current segment index.
        current_data_idx: Current data index.
    """
    def __init__(self, in_dir):
        """Initialize recorded stream.
        
        Loads the segment names and initializes other variables.
        
        Args:
            in_dir: Input data directory."""
        if not os.path.isdir(in_dir):
            raise Exception('Directory %s does not exist.' % in_dir)
        self.done = False
        self.in_dir = in_dir
        self.seg_names=[v for v in sorted(os.listdir(in_dir)) if os.path.isdir(os.path.join(in_dir,v))]
        self.data, self.times, self.time_strs = [[None for v in self.seg_names] for i in range(3)]
        self.current_seg_idx, self.current_data_idx = 0, -1
        #self.updateCurrent() # TODO(jake): should have this here, not in derived, but uses derived functionality

    def init(self, s_idx):
        """Initialize the times for the specified segment.
        
        Args:
            s_idx: Segment index to initialize."""
        time_fname = join(self.in_dir, self.seg_names[s_idx], "times.txt")
        self.time_strs[s_idx] = [v.strip() for v in open(time_fname)]
        self.times[s_idx] = map(timeStringToDateTime, self.time_strs[s_idx])

    def numSegments(self):
        """Number of segments.
        
        Returns:
           Number of recorded segments
        """
        return len(self.times)

    def getSegmentIndex(self, seg_name):
        """Get the segment index for the given segment name (time string).
        
        Returns:
           Segment index.
        """
        return self.seg_names.index(seg_name)
        
    def numSegmentData(self, s_idx):
        """Number of data for the specified segment.
        
        Args:
           s_idx: Segment index.
        
        Returns:
           Number of data for the segment.
        """
        if self.times[s_idx]==None: self.init(s_idx)
        return len(self.times[s_idx])

    def getTime(self, s_idx, d_idx):
        """Time for the given segment and data indices.
        
        Args:
           s_idx: Segment index.
           d_idx: Data index.
        
        Returns:
           Time.
        """
        if self.times[s_idx]==None: self.init(s_idx) # initialize if necessary
        return self.times[s_idx][d_idx]
        
    def getData(self, s_idx, d_idx):
        """Data for the given segment and data indices.
        
        Args:
           s_idx: Segment index.
           d_idx: Data index.
        
        Returns:
           Data.
        """
        if self.times[s_idx]==None: self.init(s_idx) # initialize if necessary
        return self.data[s_idx][d_idx]
        
    def nearestSegmentAndIndexToTime(self, t):
        """Nearest segment and data indices to the given time.
        
        Args:
           t: Time.
        
        Returns:
           Segment and data indices (as a tuple).
        """
        seg_inds = [(v,self.nearestIndexToTime(v,t)) for v in range(self.numSegments())]
        ts = [(self.getTime(s_idx,d_idx), s_idx, d_idx) for (s_idx,d_idx) in seg_inds]
        return sorted([(abs(t-v),s_idx,d_idx) for (v, s_idx, d_idx) in ts])[0][1:]
        
    def nearestIndexToTime(self, s_idx, t):
        """Nearest data index to the given time for the given segment.
        
        Args:
           s_idx: Segment index.
           t: Time.
        
        Returns:
           Data index (as a tuple).
        """
        if self.times[s_idx]==None: self.init(s_idx) # initialize if necessary
        tv = self.times[s_idx] # time vector
        if t > tv[-1]:
            return len(tv)-1
        # Below gets the closest index (accounting for edge cases).
        i = bisect.bisect_left(tv, t)
        return i if (not i or abs(tv[i-1]-t) > abs(tv[i]-t)) else i-1

    def getDataAtTime(self, s_idx, t):
        """Nearest data to the given time for the given segment.
        
        Args:
           s_idx: Segment index.
           t: Time.
        
        Returns:
           Data.
        """
        return self.getData(s_idx, self.nearestIndexToTime(s_idx, t))

    def getCurrentData(self):
        """Current data.
        
        Returns:
           Current data.
        """
        return self.getData(self.current_seg_idx, self.current_data_idx)

    def getCurrentTime(self):
        """Current time.
        
        Returns:
           Current time.
        """
        return self.getTime(self.current_seg_idx, self.current_data_idx)

    def updateCurrent(self):
        """Updates current.
        
        Updates internal pointers to current segment and data.
        If we cannot update, the internal pointers remain unchanged
        and the done flag is set.        
        """
        t = self.getCurrentTime() if self.current_data_idx >= 0 else None
        # Copy indices so that we never say the data is ready when in fact it's bad.
        si, di = self.current_seg_idx, self.current_data_idx
        while True:
            # Go to next segment if no more data for current segment
            if di >= self.numSegmentData(si)-1:
                si, di, self.has_data = si+1,-1,False
                if si < self.numSegments():
                    continue
                else: # no more data
                    self.done = True
                    return
            else: # go to next data if more
                di, self.has_data = di+1, True
                if t==None or self.getTime(si, di) > t: break
        self.current_seg_idx, self.current_data_idx = si, di

    def release(self):
        """Releases nothing as recorded stream has no resources."""
        return
