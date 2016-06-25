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

Program that calls aruco_create_marker to create markers in the specified
range of the specified dimension.
"""
import sys, os, argparse, itertools
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.tex_utils import *
from kitchen import *

if __name__ == "__main__":
        
        parser = argparse.ArgumentParser(description='Script to make markers.')
        parser.add_argument("--output", help="Output stem.", default=MARKERS_STEM)
        parser.add_argument("--start-id", help="ID start.", type=int, default=0)
        parser.add_argument("--end-id", help="ID end.", type=int, default=32)
        parser.add_argument("--dimensions", help="List of dimensions.", \
                            type=float, nargs="+", default=[3.0])
        args = parser.parse_args()
        
        tf = TexFile(args.output)
        #tf.usePackage("tikz")
        tf.usePackage("geometry", margin="1in")
        tf.usePackage("graphicx")
        tf.beginDocument()
        for (dim_idx, dim) in enumerate(args.dimensions):
                for i in range(args.start_id, args.end_id):
                        fname = "/tmp/%d-%d.png" %(dim_idx, i)
                        os.system("%s %d %s" % (join(BIN_DIR, "aruco_create_marker"), i, fname))
                        tf.includeGraphic(fname, width="%fin"%dim)
                        tf.write("~~~~~~Marker %s (%.3f in) \n" % (i, dim))
                        tf.write("\\\\ \\\\ \\\\ \\\\ \n")
        tf.endDocument()
        tf.close()
        tf.compile()
