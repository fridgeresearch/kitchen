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

Module that provides interfaces for using Aruco library.
"""
import sys, os, numpy as np, random, cv2, time, threading
from os.path import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from utils.general_utils import *

class Marker:
    """Class storing an Aruco marker.
    
    Attributes:
        id: marker id.
        corners: marker corners
    """
    def __init__(self, marker_id, corners):
        """Initialize the Marker."""
        self.id = marker_id
        self.corners = corners        
    def draw(self, im, color=(0,0,255)):
        """Draws the marker on the provided image.
        
        Args:
            im: Input / output image to draw on.
            color: Color to draw.
        """
        # Draw lines between corners and circles around the first and last.
        x = list(self.corners.astype(int))
        [cv2.line(im, tuple(u), tuple(v), color, 5) for (u,v) in zip(x, x[1:]+[x[0]])]
        cv2.circle(im, tuple(x[0]), 5, thickness=1, color=(255,255,255))
        cv2.circle(im, tuple(x[-1]), 5, thickness=1, color=(0,0,0))
        center = np.mean(x, axis=0).astype(int)
        center[0] -= 10
        cv2.putText(im, str(self.id), tuple(center), cv2.FONT_HERSHEY_SIMPLEX, 1.25, color, thickness=3)

class MarkerDetector:
    """Class providing interface to Aruco MarkerDetector."""
    def detect(self, im, detect_candidates=False):
        """Detects markers in the given image.
        
        Args:
            im: Input image.
            detect_candidates: Whether or not to return candidates as well as
                successful detections
        Returns:
            List of markers.
        """
        # Make system call that specifies where to write temporary
        # image and qr code files.
        im_fname = "/tmp/%d-qr.jpg" % random.randint(1,1024)
        qrs_fname = "/tmp/%d-qr.txt" % random.randint(1,1024)
        cv2.imwrite(im_fname, im)
        os.system("%s %s %d 0 >%s" % (os.path.join(BIN_DIR, "aruco_detect"), \
                                      im_fname, detect_candidates, qrs_fname))
        # Load markers from temporary files.
        markers = []
        for toks in [v.strip().split() for v in open(qrs_fname)]:
            marker_id, corners = int(toks[0]), np.array(toks[1:]).astype(float).reshape(-1, 2)
            markers.append(Marker(marker_id, corners))
        map(os.remove, [im_fname, qrs_fname])
        return markers
