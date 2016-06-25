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
import argparse, os, sys, json, math, numpy as np
from fractions import Fraction
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from utils.general_utils import *
from utils.math_utils import *
from utils.tex_utils import *
from config.fridge_config import *

def frac(x, y=8):
        x = x+1e-8
        whole, partial = int(x), x-int(x)
        return ("%d " % whole if whole else "") + "%s"%Fraction(round(partial*y)/y)

if __name__ == "__main__":
        
        desc = "Parse no markers config file and output complete config file and markers file."
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument("--input", help="Input configuration.", default=FRIDGE_NO_MARKERS_CONFIG)
        parser.add_argument("--output-config", help="Output config.", default=FRIDGE_FULL_CONFIG)
        parser.add_argument("--output-markers", help="Output markers.", default=MARKERS_STEM)
        parser.add_argument("--main-marker-size", help="Main marker size.", default="3.0 in")
        parser.add_argument("--door-marker-size", help="Door marker size.", default="2.0 in")
        parser.add_argument("--buffer", help="Buffer around QR code.", default="0.125 in")
        args = parser.parse_args()
        
        tf = TexFile(args.output_markers)
        tf.usePackage("geometry", margin="1in")
        tf.usePackage("graphicx")
        tf.usePackage("xcolor")
        tf.beginDocument()
        
        fridge_config = FridgeConfig(args.input)
        config = convertToStrings(json.loads(open(args.input).read()))
        mid = 0
        for section_name in ["main", "door"]: # ensure proper order
                buff = parseMeasure(args.buffer) if section_name == "door" else 0.0
                marker_sz = parseMeasure(args.main_marker_size if section_name=="main" else args.door_marker_size)
                section = fridge_config.sections[section_name]
                config["fridge"]["sections"][section_name]["markers"] = {}
                for (surface_name, surface) in section.surfaces.items():
                        for (scale_name, scale) in surface.scales.items():
                                sz = marker_sz + 2*buff
                                for zo in ["front", "center", "back"]:
                                        depth = scale.d
                                        if "main-shelf" in surface_name and surface_name[-1] != "0":
                                                depth -= inchesToMeters(1.0)
                                        if (zo=="center" and scale.d<sz*3) or (zo=="back" and scale.d<sz*2): continue
                                        dz = (0 if zo=="front" else (depth-sz if zo=="back" else depth/2-sz/2))
                                        z = scale.T_self_in_world[2, 3] + dz + buff
                                        for xo in ["left", "center", "right"]:
                                                dx = (0 if xo=="left" else \
                                                      (scale.w-sz if xo=="right" else scale.w/2-sz/2))
                                                x = scale.T_self_in_world[0, 3] + dx + buff
                                                y = scale.T_self_in_world[1, 3]
                                                # Write marker to tex file.
                                                fname = "/tmp/%d.png" % mid
                                                os.system("%s %d %s" % \
                                                          (os.path.join(BIN_DIR, "aruco_create_marker"), mid, fname))
                                                tf.includeGraphic(fname, width="%f in"%metersToInches(marker_sz), \
                                                                  border="%.3f in"%metersToInches(buff))
                                                tf.write("\\\\%s %s, Marker %d (%s, %s)\n" % \
                                                         (surface_name, scale_name, mid, \
                                                          frac(metersToInches(dx)), frac(metersToInches(dz))))
                                                tf.write("\\\\ \\\\ \\\\ \\\\ \n")
                                                # Add marker data to config file.
                                                m = {}
                                                m["x"], m["y"], m["z"] = ["%.3f in"%metersToInches(v) for v in [x,y,z]]
                                                m["dx"], m["dz"] = ["%.3f in"%metersToInches(v+buff) for v in [dx,dz]]
                                                m["roll"], m["pitch"], m["yaw"] = ["%.1f deg"%v for v in [90, 0, 0]]
                                                m["size"] = "%.1f in" % metersToInches(marker_sz)
                                                m["scale"] = scale_name
                                                config["fridge"]["sections"][section_name]["markers"][mid] = m
                                                mid += 1
        
        # Write json data.
        json.dump(config, open(args.output_config, "w"),
                  sort_keys=True, indent=2, separators=(',', ': '))

        # End, close, and compile tex.
        tf.endDocument()
        tf.close()
        tf.compile() 
        
