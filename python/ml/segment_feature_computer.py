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
import os, sys, cv2, caffe, numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from caffe_feature_computer import *
from utils.general_utils import *

class SegmentFeatureComputer:
    def __init__(self):
        self.fc7 = CaffeFeatureComputer(layer="fc7")
        self.idx = 0
    def compute(self, segment, center_of_mass, top, im, im_bg, im_cal, edges, diff_im_bg, diff_im_cal, diff_edges_bg, diff_edges_cal):
        diff_ims = [diff_im_bg, diff_im_cal, diff_edges_bg, diff_edges_cal]
        b = np.clip([segment.box[0]-50, segment.box[1]+50], (0,0), np.array(edges.shape)-1)
        ims = [convertToBgr(v) for v in [im, im_bg, edges] + diff_ims]
        ims = [v[b[0][0]:b[1][0], b[0][1]:b[1][1]] for v in ims]
        fc7_ftrs = [self.fc7.compute(v) for v in ims]
        x = [v for (i,v) in enumerate(fc7_ftrs) if i!=1] # fc7 ftrs (besides im_bg)
        x.append(np.array([np.linalg.norm(center_of_mass - segment.center())])) # distance to com
        x.append(np.array([np.linalg.norm(fc7_ftrs[0]-fc7_ftrs[1])])) # between im and im_bg ftrs
        # TODO: global features about quality of alignment
        vis = tileImages([im, 0*im, edges, im_bg, diff_im_bg, diff_edges_bg, im_cal, diff_im_cal, diff_edges_cal])
        vis = resize(vis, 1.0/4)
        cv2.imwrite("ftrs%d.png"%self.idx, vis)
        self.idx += 1
        cv2.imshow("vis", vis)
        cv2.waitKey(0)
        return np.hstack(x)
        
