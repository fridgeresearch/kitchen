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
import os, argparse
from os.path import *

STAR_DIR = join(dirname(dirname(abspath(__file__))), "public", "icons", "stars")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--output", help="Output directory.", default=STAR_DIR)
    args = parser.parse_args()
    
    for i in range(0, 51, 5):
        rating = i / 10.0
        full, half, empty = int(rating), int(rating+0.5)-int(rating), 5-int(rating+0.5)
        stars = " ".join([join(STAR_DIR, "full-star.svg")]*full) + " "
        stars = stars + " ".join([join(STAR_DIR, "half-star.svg")]*half) + " "
        stars = stars + " ".join([join(STAR_DIR, "empty-star.svg")]*empty)
        fpath = join(args.output, ("stars-%0.1f"%rating).replace(".","-")+".jpg")
        os.system("montage %s -tile 5x1 -geometry +2+0 %s" % (stars, fpath))
        
