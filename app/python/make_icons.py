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
import os, argparse, cv2, numpy as np
from os.path import *

PROGRESS_DIR = join(dirname(dirname(abspath(__file__))), "public", "icons", "progress")

def angleBetween(v1, v2):
    v1_n = np.linalg.norm(v1)
    v1_u = v1 / v1_n if v1_n else v1
    v2_n = np.linalg.norm(v2)
    v2_u = v2 / v2_n if v2_n else v2
    angle = np.arccos(np.dot(v1_u, v2_u))
    if np.isnan(angle):
        return 0.0 if (v1_u == v2_u).all() else np.pi
    return angle

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--size", help="Icon size.", type=int, default=100)
    parser.add_argument("--output", help="Output directory.", default=PROGRESS_DIR)
    args = parser.parse_args()
    
    thick = 5
    rad = args.size/2.0
    for percent in range(0, 101, 5):
        fname = join(args.output, "progress-%03d.png"%percent)
        print("Creating %s"%fname)
        im = np.zeros((args.size,args.size,4), dtype=np.uint8)
        for y in range(args.size):
            for x in range(args.size):
                p = np.array([y, x])
                c = np.array([args.size/2.0, args.size/2.0])
                a = p-c
                r = np.linalg.norm(a)
                b = np.array([args.size/2-r, args.size/2])-c
                angle = angleBetween(a, b)
                if x <= args.size/2:
                    angle = np.pi + (np.pi-angle)
                if r<=rad and (angle/(2*np.pi) <= percent/100.0 or r>=rad-thick):
                    im[y, x] = [0, 0, 255, 255]
                elif r<=rad:
                    im[y, x] = [255, 255, 255, 255]
        cv2.imwrite(fname, im)
