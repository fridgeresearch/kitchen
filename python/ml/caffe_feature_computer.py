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
import os, sys, caffe, numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *

class CaffeFeatureComputer(object):
    """Caffe feature computer

    Parameters
    ----------
    layer : string, default: 'fc7'
        Layer in conv net to use for features.

    Notes
    -----
    Uses pretrained Caffe model to extract features for an input image.
    """
    def __init__(self, layer="fc7"):
        net = "bvlc_reference_caffenet"
        self.caffe_model_dir = os.path.join(CAFFE_DIR, "models", net)
        self.caffe_model_fname = os.path.join(self.caffe_model_dir, net+".caffemodel")
        self.train_val_fname = os.path.join(self.caffe_model_dir, "deploy.prototxt")
        self.layer = layer
        self.net = caffe.Net(self.train_val_fname, self.caffe_model_fname, caffe.TEST)
        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_transpose('data', (2,0,1))
        mean_im_fname = "%s/python/caffe/imagenet/ilsvrc_2012_mean.npy" % CAFFE_DIR
        self.transformer.set_mean('data', np.load(mean_im_fname).mean(1).mean(1))
        self.net.blobs['data'].reshape(1,3,227,227)
    def eval(self, im):
        """Compute feature vector for the input image."""
        self.net.blobs['data'].data[...] = self.transformer.preprocess('data', im)
        out = self.net.forward()
        return self.net.blobs[self.layer].data[0].flatten()
