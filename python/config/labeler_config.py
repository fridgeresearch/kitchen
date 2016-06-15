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
import sys, os, json
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.general_utils import *
from kitchen import *

class LabelerConfig:
    def __init__(self, config_fname):
        config = convertToStrings(json.loads(open(config_fname).read())) if config_fname else {}
        scales_config_path = config["scales-config"] \
                             if "scales-config" in config else SCALES_CONFIG
        self.scales_config = convertToStrings(json.loads(open(scales_config_path).read()))
        self.antennas, self.barcodes, self.cameras, self.scales = {}, {}, {}, {}
        self.name = "labeler"
        labeler = config[self.name] if self.name in config else {}
        self.audio = labeler["audio"] if "audio" in labeler else {}
        self.antennas = labeler["antennas"] if "antennas" in labeler else {}
        self.barcodes = labeler["barcodes"] if "barcodes" in labeler else {}
        self.bles = labeler["bles"] if "bles" in labeler else {}
        self.cameras = labeler["cameras"] if "cameras" in labeler else {}
        self.keyboards = labeler["keyboards"] if "keyboards" in labeler else {}
        self.scales = labeler["scales"] if "scales" in labeler else {}
        self.load_cells = dict([("%s-%d"%(v,w),{}) for v in self.scales.keys() for w in range(3)])
        self.recording_streams = dict([("AudioStream", self.audio.keys()),
                                       ("BarcodeStream", self.barcodes.keys()),
                                       ("BleStream", self.bles.keys()),
                                       ("CameraStream", self.cameras.keys()),
                                       ("KeyboardStream", self.keyboards.keys()),
                                       ("LoadCellStream", self.load_cells.keys()),
                                       ("RfidAntennaStream", self.antennas.keys())])
