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
import sys, os, cv2, numpy as np, pickle
from os.path import *
from itertools import combinations as itc
sys.path.append(dirname(dirname(abspath(__file__))))
from extrinsics.aruco import *

class ExtrinsicCalibration:
    """Class for extrinsic calibration.
    
    Non-parametric extrinsic calibration that maps from marker locations to 
    camera poses. Calibration operations on image sets (at a given time,
    one image per camera).
    
    Attributes:
        fridge_config: Fridge model.
        md: Aruco MarkerDetector.
        markers: Vector of ArucoMarkers for calibration image sets.
        transforms: Vector of transforms for calibration image sets.
        times: Vector of times for calibration image sets.
    """
    def __init__(self, fridge_config, fname=None):
        """Initialize the calibration."""
        self.fridge_config, self.md = fridge_config, MarkerDetector()        
        self.markers, self.transforms, self.times = [], [], []
        if fname: self.load(fname)

    def save(self, fname):
        """Save the calibration to a Pickle."""
        if splitext(fname)[1] != ".pkl":
            raise Exception("ExtrinsicCalibration archive must be a pickle.")
        pickle.dump((self.markers, self.transforms, self.times), open(fname, "w"))

    def load(self, fname):
        """Load the calibration from a Pickle."""
        if splitext(fname)[1] != ".pkl":
            raise Exception("ExtrinsicCalibration archive must be a pickle.")
        self.markers, self.transforms, self.times = pickle.load(open(fname, "r"))
                    
    def _markerDist(self, a, b):
        """Compute distance between two markers' centroids."""
        dists = [np.linalg.norm(np.mean(v.corners,axis=0)-np.mean(w.corners,axis=0)) \
                 for v in a for w in b if v.id==w.id]
        return min(dists) if dists else 1e8

    def update(self, time, ims):
        """Update calibration (transforms, markers, and times)."""
        if time in self.times: return
        N = len(self.fridge_config.cameras.items())
        if len(ims) != N: raise Exception("ExtrinsicCalibration update() expects %d images." % N)
        transforms, markers = [], []
        for im in ims:
            all_detected = self.md.detect(im)
            calib = [(m, m_el) for m in all_detected for (m_id, m_el) in self.fridge_config.markers.items()\
                     if int(m_id)==m.id]
            noncalib = [v for v in all_detected if v.id not in map(int, self.fridge_config.markers.keys())]
            cur_transform, cur_markers = None, noncalib
            for combo in [w for v in xrange(len(calib),2,-1) for w in itc(calib,v)]:
                combo_markers, marker_els = zip(*combo)
                combo_corners = np.array([v.corners for v in combo_markers]).reshape(-1,2)
                pts = np.array([v.T_self_in_world.dot(v.points_in_self)[:3, :].T \
                                for v in marker_els]).reshape(-1,3)
                r, rv, tv = cv2.solvePnP(pts, combo_corners, CAMERA_CMAT, CAMERA_DCOEFFS)
                ip = cv2.projectPoints(pts, rv, tv, CAMERA_CMAT, CAMERA_DCOEFFS)[0].reshape(-1,2)
                perror = np.linalg.norm((ip-combo_corners)) / ip.shape[0]
                if perror < 5:
                    R = cv2.Rodrigues(rv)[0]
                    T_world_in_camera = getTransformFromRt(R, tv) # since marker positions in world coords
                    cur_markers = list(combo_markers) + noncalib
                    cur_transform = T_world_in_camera
                    break
            transforms.append(cur_transform)
            markers.append(cur_markers)
        self.transforms.append(transforms)
        self.markers.append(markers)
        self.times.append(time)

    def delete(self, time):
        """Delete the calibration data at the given time."""
        if time in self.times:
            idx = self.times.index(time)
            del self.times[idx], self.transforms[idx], self.markers[idx]

    def getData(self, time):
        """Get the calibration data at the given time."""
        if time in self.times:
            idx = self.times.index(time)
            return self.transforms[idx], self.markers[idx]
        else:
            N = len(self.fridge_config.cameras.items())
            return [None for v in range(N)], [[] for v in range(N)]

    def predict(self, ims):
        """Return nearest neighbor transforms and query markers."""
        N = len(self.fridge_config.cameras.items())
        if len(ims) != N: raise Exception("ExtrinsicCalibration predict() expects %d images." % N)
        nn_dists, nn_transforms = [1e8 for v in range(N)], [None for v in range(N)]
        query_markers = [self.md.detect(im) for im in ims]
        for (markers, transforms) in zip(self.markers, self.transforms):
            dist = min([self._markerDist(*v) for v in zip(query_markers, markers)])
            for i in range(N):
                if dist < nn_dists[i] and dist < 50.0 and transforms[i] != None:
                    nn_dists[i], nn_transforms[i] = dist, transforms[i]
        return nn_transforms, query_markers
