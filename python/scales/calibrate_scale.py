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

Calibrate scale.
"""
import argparse, sys, os
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from scales.scale_calibration import *
from scales.scale_utils import *
from config.fridge_config import *
from utils.general_utils import *
from utils.tex_utils import *
from data_stream.stream_utils import *

if __name__ == "__main__":

	# Example run: python 
        parser = argparse.ArgumentParser(description='Fit scale calibration.')
        parser.add_argument("--scale", help="Scale", required=True)
        parser.add_argument("--input", help="Input directory", default=SCALES_CALIBRATION_DATA)
        parser.add_argument("--test-weights", help="Test weights.", type=int, \
                            nargs="+", default=[100,200,500,1000])
        parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG)
        parser.add_argument("--output", help="Output stem")
        args = parser.parse_args()
        
        fridge_config = FridgeConfig(args.config)
        width = metersToMillimeters(fridge_config.scales[args.scale].w)
        height = metersToMillimeters(fridge_config.scales[args.scale].d)
        template_name = fridge_config.scales[args.scale].template
        template = np.load(join(SCALES_CONFIG_DATA, "%s.npy"%template_name))
        positions = inchesToMillimeters(template[::-1, :].reshape(-1,2))
        # Set origin at one 1in up from the bottom and centerd 
        # (so between the two base load cells).
        #ox, oy = width/2, height/2
        ox, oy = width/2, inchesToMillimeters(1.0)
        #ox, oy = 0, 0
	positions[:,0] -= ox
	positions[:,1] -= oy
        # Data.
        fnames, X, Y = [], [], []
        #Y = [np.hstack((pos, int(v.split('-')[-2])*np.ones((pos.shape[0],1)))) for v in args.input_data]
        for weight in args.test_weights:
                weight_path = join(args.input, "%dg"%weight)
                if exists(weight_path):
                        try:
                                s = ScaleStreamRecorded(weight_path, args.scale)
                        except Exception as e: # TODO(jake): catch specific exception
                                print e
                                continue
                        fnames.append(weight_path)
                        for s_idx in range(s.numSegments()):
                                x, y = [], []
                                event_times = extractEventTimes(s, s_idx)[1:] # TODO: remove when fix data
                                tare_t = event_times[0][2]
                                print len(event_times), len(positions), weight_path
                                if len(event_times)!=len(positions):
                                        print "skipping!"
                                        continue
                                assert(len(event_times)==len(positions))
                                for (pos, (_, _, _, _, _, t)) in zip(positions, event_times):
                                        tare = np.array(s.getDataAtTime(s_idx, tare_t))
                                        data = np.array(s.getDataAtTime(s_idx, t))
                                        x.append(data-tare)
                                        y.append((pos[0], pos[1], weight))
                                X.append(x)
                                Y.append(y)
                                #break
                        #break
        
        # Output calibration.
	if not args.output: args.output = join(SCALES_MODELS, args.scale)

        # Fit the calibration model.
        cal = ScaleCalibration()
        X_mat, Y_mat = np.vstack(X), np.vstack(Y)
        cal.fit(np.vstack(X), np.vstack(Y))
        Y_pred_mat = map(cal.predict, X_mat)
        residuals = abs(Y_mat - Y_pred_mat)
        #for (x, y, y_pred, r) in zip(X_mat, Y_mat, Y_pred_mat, residuals):
        #        print x, y.astype(int), r.astype(int)
        cal.save("%s.txt"%args.output)

        # Visualize calibration results.
        order = 0
        if True:#args.visualize:
                tf = TexFile(args.output)
                tf.paperWidth(millimetersToInches(width)+4.0, units="in")
                tf.paperHeight(millimetersToInches(height)+4.0, units="in")
                tf.usePackage("tikz")
                tf.usePackage("geometry", margin="1.0in")
                tf.beginDocument()
                all_rs = []
                for (fname, x, y) in zip(fnames, X, Y):
                        rs = []
                        tf.beginTikzPicture(xscale="1mm", yscale="1mm")
                        tf.drawEmptyRectangle((0,0), height, width)
                        tf.drawLine((ox, 0), (ox, height), color="blue")
                        tf.drawLine((0, oy), (width, oy), color="blue")
                        for (xi, yi) in zip(x, y):
                                yi_p = cal.predict(xi)
                                r = cal.predict(xi)-yi
                                #print yi, yi_p
                                for ((cx,cy,cf), color) in [(yi,"black"),(yi_p,"red")]:
					tf.drawCircle((cx+ox, cy+oy), 5, color=color)
                                        tf.drawText((cx+ox, cy+oy+10), order, color=color)
                                        if color == "black": tf.drawText((cx+ox,cy+oy), (int(cx),int(cy)))
                                order += 1
                                rs.append(yi_p-yi)
                        all_rs += rs
                        rs = np.array(rs)
                        ar = np.mean(np.sqrt(rs*rs), axis=0)
                        #print "Average residuals for %s = %s" % (fname, str(ar))
                        tf.endTikzPicture()
                        tf.write("\\clearpage\n")
                all_rs = np.array(all_rs)
                print "Average residuals =", np.mean(np.sqrt(all_rs*all_rs), axis=0)
                print "Max residuals =", np.max(np.abs(all_rs), axis=0)
                tf.endDocument()
                tf.close()
                tf.compile()
