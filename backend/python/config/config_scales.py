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
from utils.tex_utils import *
from utils.math_utils import *

def myRound(x, y=4):
        """Rounds floating point number to specified number of decimal places."""
        return round(x*y)/y

def locationString(w):
        """Creates location string from location vector."""
        d = map(int, w)
        f = w[0]-d[0], w[1]-d[1]
        s = "%d%s\",~%d%s\"" % (d[0], " %s"%Fraction(f[0]) if f[0] else "",
                            d[1], " %s"%Fraction(f[1]) if f[1] else "")
        return s

def writeSurfaceData(tf, surface_name, surface_data):
        """Writes surface data to tex file."""
        # Get bottom/upper left/right (innermost for two components)
        bls, brs, uls, urs = [], [], [], []
        min_x, max_x, min_y, max_y = 1e4, -1e4, 1e4, -1e4
        for (comp_name, verts) in surface_data["components"].items():
                [cmin_x, cmax_x], [cmin_y, cmax_y] = [[f(verts, key=lambda x: x[v])[v] \
                                                       for f in [min,max]] for v in [0,1]]
                bl, br = [f([v for v in verts if v[1]==cmin_y]) for f in [min,max]]
                ul, ur = [f([v for v in verts if v[1]==cmax_y]) for f in [min,max]]
                bls.append(bl); brs.append(br); uls.append(ul); urs.append(ur)
                min_x, min_y = min(min_x, cmin_x), min(min_y, cmin_y)
                max_x, max_y = max(max_x, cmax_x), max(max_y, cmax_y)
                if comp_name=="top": # Get calibration positions
                        height, width = ul[1]-bl[1], ur[0]-ul[0]
                        rows = min(args.max_cal_dim, max(args.min_cal_dim, int(height/2.0)))
                        cols = min(args.max_cal_dim, max(args.min_cal_dim, int(width/2.0)))
                        cell_h, cell_w = height/rows, width/cols
                        # Compute pos, array of test weight positions in top's coordinate system.
                        #pos = np.array([[[x*cell_w+cell_w/2+ul[0]-width/2,y*cell_h+cell_h/2-height/2] \
                        pos = np.array([[[x*cell_w+cell_w/2+ul[0],y*cell_h+cell_h/2] \
                                         for x in range(cols)] for y in range(rows)]) # if not centered
        # Compute scaling factor for laser cutting drawings (1.0 if using Room 36)
        scale = myRound(max((max_x-min_x+6.0)/args.paper_width, (max_y-min_y+6.0)/args.paper_height), 4)
        bl = [max([v[0] for v in bls]), max([v[1] for v in bls])]
        br = [min([v[0] for v in brs]), max([v[1] for v in brs])]
        ul = [max([v[0] for v in uls]), min([v[1] for v in uls])]
        ur = [min([v[0] for v in urs]), min([v[1] for v in urs])]
        bl, br, ul, ur = map(np.array, [bl, br, ul, ur])
        # Use to get screw locations (note that these are in combined coordinate system)
        assert((bl[0]+br[0])/2.0 == (ul[0]+ur[0])/2.0)
        cx, cy = (bl[0]+br[0])/2.0, (bl[1]+ul[1])/2.0
        hyp, diam = 40.0/25.4, 5.0/25.4 # TODO: don't hard code
        # - Outter screw locations 
        buff = surface_data["buffer"]
        outter = bl+buff, [br[0]-buff, br[1]+buff], np.array([cx, ul[1]-buff])
        screw_locs = [[myRound(w, 16) for w in v] for v in outter]
        # - Inner screw locations
        for (x, y) in outter:
                theta = math.atan((1.0*cy-y)/(cx-x)) if cx!=x else 3.0/2*math.pi
                if theta <= 0 and y<=cy: theta = theta + math.pi
                dx, dy = hyp*math.cos(theta), hyp*math.sin(theta)
                screw_locs.append((myRound(x+dx, 16), myRound(y+dy, 16)))
        # Draw the scaled components
        for (component_name, verts) in surface_data["components"].items():
                name = "%s-%s"%(surface_name, component_name)
                tf.f.write("NAME: %s, COUNT: %d\\\\ \\\\ \n" % (name, surface_data["count"]))
                tf.beginTikzPicture(xscale="1in", yscale="1in")
                # Draw the components vertices.
                for (u, v) in zip(verts, verts[1:]+[verts[0]]):
                        tf.drawLine(np.array(u)/scale, np.array(v)/scale)
                        for w in [u, v]:
                                # Have location string be in this piece's coordinate system (so all at 0,0).
                                s = locationString([w[0]-verts[0][0], w[1]-verts[0][1]])
                                delta = 0.0
                                if ("main-shelf" in surface_name and len(verts)>=6) and \
                                   w in [verts[2], verts[5]]:
                                        delta = 0.5                         
                                tf.drawText(np.array([w[0], w[1]-delta])/scale, s)
                # Draw screw locations
                r = [0,3] if component_name=="top" else [3,6]
                for screw_loc in screw_locs[r[0]:r[1]]:
                        tf.drawCircle(np.array(screw_loc)/scale, diam/scale, color="red")
                        # Again, location string in this piece's coordinate system.
                        s = locationString([screw_loc[0]-verts[0][0], screw_loc[1]-verts[0][1]])
                        tf.drawText((screw_loc[0]/scale, (screw_loc[1]-0.5)/scale), s, color="red")
                tf.endTikzPicture()
                tf.f.write("\\clearpage\n")
        # Draw the full-size calibration components in pieces.
        piece_width, piece_height = args.paper_width-2.0, args.paper_height-2.0
        verts = surface_data["components"]["top"]
        verts = [(v[0]-verts[0][0], v[1]-verts[0][1]) for v in verts]
        name = "%s-top"%surface_name
        for dim in args.diameters:
                for y in range(4):
                        for x in range(4):
                                lines = []
                                y_range = np.array([y, y+1])*piece_height
                                x_range = np.array([x, x+1])*piece_width
                                for (u, v) in zip(verts, verts[1:]+[verts[0]]):
                                        u = np.clip(u, [x_range[0], y_range[0]], [x_range[1], y_range[1]])
                                        v = np.clip(v, [x_range[0], y_range[0]], [x_range[1], y_range[1]])
                                        if (u!=v).any(): lines.append((u, v))
                                #x_range, y_range, d = x_range-width/2, y_range-height/2, dim/2
                                d = dim/2 # If not centered
                                piece_pos = [v for w in pos for v in w \
                                             if v[0]>=x_range[0]-d and v[0]<=x_range[1]+d and \
                                             v[1]>=y_range[0]-d and v[1]<=y_range[1]+d]
                                if len(piece_pos):
                                        tf.f.write("Component name: %s-%d-%d\\\\ \\\\  \n" % (name, y, x))
                                        tf.beginTikzPicture(xscale="1in", yscale="1in")
                                        [tf.drawLine(np.array(u), np.array(v)) for (u,v) in lines]
                                        for p in piece_pos:
                                                x_pos, y_pos = [int(inchesToMillimeters(v)) for v in [p[0], p[1]]]
                                                #p = p[0]+width/2, p[1]+height/2
                                                p = p[0], p[1] # If not centered
                                                tf.drawCircle(p, dim/2)
                                                tf.drawText(p, "\\large (%d,%d)" % (x_pos, y_pos))
                                        tf.endTikzPicture()
                                        tf.f.write("\\clearpage\n")
        return pos

if __name__ == "__main__":
        
        desc = "Parse scale config file and output templates."
        parser = argparse.ArgumentParser(description=desc)
        parser.add_argument("--input", help="Input configuration.", default=SCALES_CONFIG)
        parser.add_argument("--output", help="Output directory.", default=SCALES_CONFIG_DATA)
        parser.add_argument("--diameters", help="Test weight diameters.", type=float, nargs="+", default=[1.0, 1.25, 1.65, 2.0])
        parser.add_argument("--max-cal-dim", help="Max calibration dimension.", type=int, default=5)
        parser.add_argument("--min-cal-dim", help="Max calibration dimension.", type=int, default=2)
        parser.add_argument("--paper-width", help="Paper width.", type=float, default=17.0)
        #parser.add_argument("--paper-width", help="Paper width.", type=float, default=21.0)
        parser.add_argument("--paper-height", help="Paper height.", type=float, default=11.0)
        #parser.add_argument("--paper-height", help="Paper height.", type=float, default=21.0)
        args = parser.parse_args()
        
        json_data = json.loads(open(args.input).read())
        tf = TexFile(os.path.join(args.output, "drawings"))
        tf.paperWidth(args.paper_width, units="in")
        tf.paperHeight(args.paper_height, units="in")
        tf.usePackage("tikz")
        tf.usePackage("geometry", margin="1.0in")
        tf.beginDocument()
        for (surface_name, surface_data) in json_data.items():
                #if surface_name != "main-shelf": continue
                pos = writeSurfaceData(tf, surface_name, surface_data)
                np.save("%s.npy"%os.path.join(args.output, surface_name), pos)
        tf.endDocument()
        tf.close()
        tf.compile()
