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
from scales.scale_calibration import *

class ScaleStream:
    """Class for streaming recorded scale data.
    
    Class for streaming recorded scale data. Note that a scale stream is a list
    of load cell streams with a calibration and methods for 
    computing force vectors.
    """
    def __init__(self, sn):
        """Initialize the stream.
        
        Initialize the stream given the serial number. In addition to typical
        stream initialization, also load the calibration.
        
        Args:
            sn: Serial number."""
        self.cal = ScaleCalibration()
        cal_fname = join(SCALES_MODELS, "%s.txt"%sn)
        if exists(cal_fname):
            self.cal.load(cal_fname)

    def getCurrentForceVector(self, tare_readings, warn=True):
        """Get the current force vector given the tare readings.
        
        Returns the force vector given the tare readings. Gets the current data,
        subtracts the tare readings, applies the calibration,
        and returns the result.
        
        Args:
           tare_readings: tare readings.
        
        Returns:
           A 4-dimensional (x,y,z,f) force vector.
        """
        d = np.array(self.getCurrentData())
        return d if d==None else self.cal.predict(d-tare_readings, warn)

    def getCurrentLoadCellForces(self, tare_readings=np.array([0,0,0]), warn=True):
        """Get the current forces (ignore x, y, and z) given the tare readings.
        
        Returns the forces given the tare readings. Gets the current data,
        subtracts the tare readings, applies the calibration (only for forces),
        and returns the result.
        
        Args:
           tare_readings: tare readings.
        
        Returns:
           A 3-dimensional force vector.
        """
        d = np.array(self.getCurrentData())
        return d if d==None else self.cal.predictLoadCellForces(d-tare_readings, warn)
