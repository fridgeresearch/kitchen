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
import sys, os, argparse, cv2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.general_utils import *
from extrinsics.aruco import *

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Evaluate calibration.')
    args = parser.parse_args()

    cap = cv2.VideoCapture(0)
    md = MarkerDetector()
    while True:
        im = cap.read()[1]
        #im = cv2.imread("/tmp/999-qr.jpg")
        [v.draw(im, (0,0,255)) for v in md.detect(im)]
        cv2.imshow("vis", resize(im, 1.0/4))
        if 'q'==getKey(cv2.waitKey(10)): break
