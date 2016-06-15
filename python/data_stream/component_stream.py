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

class ComponentStream:
     """Abstract class for streaming array of sensor streams.
    
     Attributes:
         model: Component (eg, Fridge or Labeler) model
         streams: Dictionary from stream type to list of streams.
     """
     def __init__(self, model):
          self.model = model
          self.streams = {}
          self.audio_streams = {}
          self.barcode_streams = {}
          self.ble_streams = {}
          self.camera_streams = {}
          self.load_cell_streams = {}
          self.rfid_antenna_streams = {}
          self.scale_streams = {}
     
     def _initSensorStreams(self):
          self.audio_streams = self.streams["AudioStream"]
          self.barcode_streams = self.streams["BarcodeStream"]
          self.ble_streams = self.streams["BleStream"]
          self.camera_streams = self.streams["CameraStream"]
          self.load_cell_streams = self.streams["LoadCellStream"]
          self.rfid_antenna_streams = self.streams["RfidAntennaStream"]
          self.scale_streams = self.streams["ScaleStream"]
