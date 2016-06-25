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

Program to record scale calibration data. Wrapper around load cell streaming.
"""
import sys, os, argparse
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Record scale calibration data.')
    parser.add_argument("--scale", help="Scale serial number", required=True)
    parser.add_argument("--test-weight", help="Test weight", type=int, required=True)
    args = parser.parse_args()
    
    load_cells = ["%s-%d"%(args.scale, v) for v in range(3)]
    load_cells_str = " ".join(load_cells)
    out_dir = join(SCALES_CALIBRATION_DATA, "%dg"%args.test_weight)
    out_dirs = " ".join([join(out_dir, "LoadCellStream%s"%v) for v in load_cells])
    cmd = "python python/scales/stream_load_cells.py --load-cells %s --data %s"
    os.system(cmd % (load_cells_str, out_dirs))
    
