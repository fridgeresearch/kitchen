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
from os.path import join
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from data_stream.component_stream import *
from data_stream.audio_stream_live import *
from data_stream.barcode_stream_live import *
from data_stream.ble_stream_live import *
from data_stream.camera_stream_live import *
from data_stream.component_stream_live import *
from data_stream.load_cell_stream_live import *
from data_stream.rfid_antenna_stream_live import *
from data_stream.scale_stream_live import *

class ComponentStreamLive(ComponentStream):
     """Class for streaming array of live sensor streams.
     
     Class for streaming array of sensor streams. Note that provides same
     interface as ComponentStreamRecorded when accessing current data.
    
     Attributes:
     """
     def __init__(self, model):
          ComponentStream.__init__(self, model)
          for (stream_name, sensor_names) in fridge_config.recording_streams.items():
               self.streams[stream_name] = dict([(v,eval(stream_name+"Live")(v)) \
                                                 for v in sensor_names])
          sns = self.model.scales.keys()
          self.streams["ScaleStream"] = dict([(v,ScaleStreamLive(v)) for v in sns])
          self.streams["LoadCellStream"] = dict([w for v in self.streams["ScaleStream"].values() \
                                                 for w in zip(v.load_cell_names, v.streams)])
          self._initSensorStreams()

     def numSegments(self):
          """Number of segments.
          
          Returns:
              Number of recorded segments
          """
          return len(self.seg_names)
     

     def getSegmentIndex(self, seg_name):
          """Get the segment index for the given segment name (time string).
        
          Returns:
              Segment index.
          """
          return self.seg_names.index(seg_name)

     """
     def getDataAtTime(self, seg_idx, t):
          return [[w.getDataAtTime(seg_idx, t) for w in v] \
                  for v in [self.scale_streams.values(), self.camera_cell_streams.values()]]
     """
