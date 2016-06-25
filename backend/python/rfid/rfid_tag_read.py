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
from utils.general_utils import *

class RfidTagRead:
    """Class for storing RFID tag read data.
    
    Attributes:
        time_str: RFID tag read acquisition time string.
        time: RFID tag read acquisition time.
        antenna: RFID antenna ID.
        freq: Frequency.
        epc: Unique EPC identifier.
        count: Detection count.
        rssi: Received Signal Strength Indicator.
        phase: Tag phase.
    """
    def __init__(self, time_str, antenna, freq, epc, count, rssi, phase):
        """Initialize tag read with all data."""
        self.time_str, self.time = time_str, timeStringToDateTime(time_str)
        self.antenna, self.freq = antenna, freq
        self.epc, self.count, self.rssi, self.phase = epc, int(count), int(rssi), int(phase)
    def __str__(self):
        return "%s %s %s %s %d %d %d" % \
            (self.time_str, self.antenna, self.freq, self.epc, self.count, self.rssi, self.phase)

class RfidPresenceClassifier:
    """Class for classifying whether or not an RFID tag is present.
    
    Attributes:
        None
    """
    def eval(self, antenna_data, stable_start, stable_end):
        score = 0.0
        for (antenna, data) in antenna_data.items():
            for (time, rssi) in data:
                score += (time>stable_start and time<stable_end)
        return score

class RfidArrivalClassifier:
    """Class for classifying whether or not an RFID tag just arrived
    
    Attributes:
        None
    """
    def eval(self, antenna_data, stable_start, stable_end):
        score = 0.0
        for (antenna, data) in antenna_data.items():
            for (time, rssi) in data:
                score += (time>stable_start and time<stable_end)
        return score

class RfidRemovalClassifier:
    """Class for classifying whether or not an RFID tag just arrived
    
    Attributes:
        None
    """
    def eval(self, antenna_data, stable_start, stable_end):
        score = 0.0
        for (antenna, data) in antenna_data.items():
            for (time, rssi) in data:
                score -= (time>stable_start and time<stable_end)
        return score
