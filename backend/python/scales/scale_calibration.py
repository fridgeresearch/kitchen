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
import os, numpy as np

class ScaleCalibration:
    """Class for scale calibration.
    
    Calibration from load cell readings to (x, y, z, Force) vector.
    
    Attributes:
        theta: Calibration matrix.
    """
    
    def __init__(self, fname=None):
        """Initialize the calibration."""
        self.theta = np.zeros((3,3))
        self.theta[:, 2] = 5e3
        self.theta_set = False
        if fname: self.load(fname)

    def load(self, fname):
        """Load the calibration from a numpy txt file."""
        if os.path.splitext(fname)[1] != ".txt":
            raise Exception("ScaleCalibration archive must be a txt file.")
        self.theta = np.loadtxt(fname)
        self.theta_set = True
    
    def save(self, fname):
        """Save the calibration to a numpy txt file."""
        if not self.initialized():
            raise Exception("ScaleCalibration is uninitialized.")
        if os.path.splitext(fname)[1] != ".txt":
            raise Exception("ScaleCalibration archive must be a txt file.")
        np.savetxt(fname, self.theta)
    
    def initialized(self):
        return self.theta_set
        
    # X[i] \in M_ix3, X[i]_{j,k} is reading on kth load cell for jth sample in ith trial.
    # - All readings assumed to be tared.
    # Y[i] \in M_ix3
    # - Y[i]_{j,0} is the x position of the jth sample in the ith trial.
    # - Y[i]_{j,1} is the y position of the jth sample in the ith trial.
    # - Y[i]_{j,2} is the force for the jth sample in the ith trial.
    def fit(self, X, Y):
        """Fit the calibration to the given data and target matrices."""
        for i in range(2): Y[:, i] *= Y[:, 2]
        self.theta = np.linalg.inv(X.transpose().dot(X)).dot(X.transpose()).dot(Y)
        self.theta_set = True
        
    # x \in R^3 is an array of tared load cell readings.
    def predict(self, x, warn=True):
        """Predict (x, y, z, Force) given the load cell readings."""
        if not self.initialized() and warn:
            raise Exception("ScaleCalibration is uninitialized.")
        r = x.dot(self.theta).reshape((3,))        
        r[:2] = r[:2]/r[2] if abs(r[2])>1e-1 else (0.0, 0.0)
        return r

    def predictLoadCellForces(self, x, warn=True):
        """Predict load cell forces given the load cell readings."""
        if not self.initialized() and warn:
            raise Exception("ScaleCalibration is uninitialized.")
        return x * self.theta[:, 2]
