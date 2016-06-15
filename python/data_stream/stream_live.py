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
import sys, os, datetime, logging
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.general_utils import *

class StreamWriter:
    """Class for writing stream data.
    
    Attributes:
        out_path: Path for output directory.
        start_time: Start time for writing.
        end_time: End time for writing.
        closed: Whether or not writers closed.
        time_file: Time output file.
        data_file: Data output file.
    """
    def __init__(self, out_path, start_time, time_buffer, **kwargs):
        """Initialize writer.
        
        Initialize the writer. Create output time and data files.
        
        Args:
            out_path: Output path.
            start_time: Start time."""
        self.time_buffer = datetime.timedelta(seconds=time_buffer)
        self.start_time = start_time - self.time_buffer
        self.end_time = None
        self.closed = False
        self.out_path = join(out_path, dateTimeToTimeString(start_time))
        if "Scale" not in self.out_path: os.makedirs(self.out_path) # TODO(jake): fix hack
        self._createTimeFile()
        self._createDataFile()
    def setEndTime(self, time):
        """Set the end time for this writer.
        
        Args:
            time: Non-buffered end time."""
        if self.endTimeIsSet():
            raise Exception("StreamWriter: end time is already set.")
        self.end_time = time + self.time_buffer
    def endTimeIsSet(self):
        """Whether or not the end time is set.
        
        Returns:
            Boolean whether or not is set."""
        return self.end_time!=None
    def close(self):
        """Close this stream."""
        self.closed = True
        self._closeTimeWriter()
        self._closeDataWriter()
        logging.info(":StreamWriter Done writing for %s" % (self.out_path,))
    def shouldClose(self, time):
        """Whether or not time to close.
        
        Args:
            time: Non-buffered end time.
        
        Returns:
            Boolean whether or not should close."""
        return self.endTimeIsSet() and time > self.end_time
    def write(self, time, data):
        """Write time and data.
        
        Args:
            time: Time to write.
            data: Data to write."""
        if time >= self.start_time and (not self.endTimeIsSet() or time <= self.end_time):
            self._writeTime(time)
            self._writeData(data)
    def _writeTime(self, time):
        """Write time to file.
        
        Args:
            time: Time to write."""
        self.time_file.write("%s\n"%dateTimeToTimeString(time))
    def _writeData(self, data):
        """Write data to file.
        
        Args:
            data: Data to write."""
        self.data_file.write(data)
    def _createTimeFile(self):
        """Create time output file."""
        self.time_file = open(join(self.out_path, "times.txt"), "w")
    def _createDataFile(self):
        """Create data output file."""
        self.data_file = open(join(self.out_path, "data.txt"), "w")
    def _closeTimeWriter(self):
        """Close the time writer."""
        self.time_file.close()
    def _closeDataWriter(self):
        """Close the data writer."""
        self.data_file.close()

class StreamLive:
    """Abstract Class for streaming live data.

    Class for streaming live data. Note that provides same interface as StreamRecorded
    when accessing current data.
    
    Attributes:
        done: Whether or not we are done streaming (always false since live)
    """
    def __init__(self, out_path=None, **kwargs):
        """Initialize live stream."""
        self.done = False
        self.out_path = out_path
        self.writers, self.writer_class = [], StreamWriter

    def getCurrentTime(self):
        """Returns current time, which is simply system time (since live)."""
        return datetime.datetime.utcnow()

    def updateCurrent(self):
        """Does nothing since live constantly updated."""
        return

    def release(self):
        """Default does nothing."""
        [v.close() for v in self.writers]

    def createWriter(self, start_time, time_buffer=0.0, **kwargs):
        if self.out_path==None:
            raise Exception("StreamLive: Unitialized output path.")
        w = self.writer_class(self.out_path, start_time, time_buffer, **kwargs)
        self.writers.append(w)
            
    def setWriterEndTimes(self, end_time):
        [v.setEndTime(end_time) for v in self.writers if not v.endTimeIsSet()]

    def write(self, time, data):
        [v.write(time, data) for v in self.writers]

    def close(self, time):
        [v.close() for v in self.writers if v.shouldClose(time)]
        self.writers = [v for v in self.writers if not v.closed]
