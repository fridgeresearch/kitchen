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
import sys, os, cv2
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_live import *
from utils.cv_utils import *

class CameraStreamWriter(StreamWriter):
    """Class for writing camera stream data.
    """
    def __init__(self, out_path, start_time, time_buffer, fps, **kwargs):
        self.fps = fps
        StreamWriter.__init__(self, out_path, start_time, time_buffer)
    def _createDataFile(self):
        fname = join(self.out_path,"vid.avi")
        fc = cv2.VideoWriter_fourcc(*'XVID')
        self.data_file = Cv2VideoWriter(fname, self.fps)

class CameraStreamLive(StreamLive):
    """Class for streaming live camera data.
    
    Class for streaming live camera data. A wrapper around a VideoCapture object.
    
    Attributes:
        cap: VideoCapture object.
    """
    def __init__(self, camera, out_path=None, shape=None, **kwargs):
        """Initialize live camera stream.
        
        Args:
            camera: VideoCapture camera index.
        """
        StreamLive.__init__(self, out_path, **kwargs)
        self.writer_class = CameraStreamWriter
        self.cap = cv2.VideoCapture(int(camera))
        self.shape = shape
        #self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        #self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        #self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        #self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if self.shape:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.shape[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.shape[1])

    def getCurrentData(self):
        """Get the current data.
        
        Get the current data returned from the VideoCapture's read() method."""
        im = self.cap.read()[1]
        if self.shape and self.shape != im.shape:
            im = cv2.resize(im, self.shape)
        return im
