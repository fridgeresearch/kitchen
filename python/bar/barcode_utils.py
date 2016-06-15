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
import sys, os, barcode, StringIO, numpy as np
from PIL import Image
from os.path import *
from dateutil.parser import parse
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from utils.general_utils import *

class Barcode:
    """Class for storing barcode data.
    
    Stores barcode data and allows user to retrieve barcode image.

    Attributes:
        time_str: Barcode acquisition time string.
        time: Barcode acquisition time.
        code: EPC code.
    """
    def __init__(self, time_str, code):
        """Initialize barcode with time and EPC code.
        
        Args:
            time_str: Time string in standard format.
            code: EPC code string.
        """
        self.time_str, self.time = time_str, timeStringToDateTime(time_str)
        self.code = code

    def __str__(self):
        return "%s %s" % (self.time_str, self.code)

    def image(self, shape=None):
        """Returns image representation of barcode.
        
        Args:
            shape: desired image shape.
        
        Returns:
            An numpy array image representation of barcode.
        """
        # Convert code to StringIO to Image to Numpy array.
        ean = barcode.get('ean', self.code, writer=barcode.writer.ImageWriter())
        str_io = StringIO.StringIO()
        ean.write(str_io)
        str_io.seek(0)
        im = np.array(Image.open(str_io).convert('RGB'))[:,:,::-1]
        # Reshape (if necessary) and pad (if necessary).
        if shape != None:
            scaling = min(1.0*shape[0]/im.shape[0], 1.0*shape[1]/im.shape[1])
            unpadded_shape = np.min((np.array(im.shape[:2])*scaling, shape), axis=0).astype(int)
            im = cv2.resize(im, tuple(unpadded_shape[::-1]))
            bottom = (shape[0] - im.shape[0])/2
            top = shape[0]-im.shape[0]-bottom
            right = (shape[1] - im.shape[1])/2
            left = shape[1]-im.shape[1]-right
            im = cv2.copyMakeBorder(im, top, bottom, left, right,
                                    borderType=cv2.BORDER_CONSTANT, value=(255,255,255))
        return im
