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
import argparse, sys, os, time, numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scales.load_cells import *

if __name__ == "__main__":
        
        parser = argparse.ArgumentParser(description='Stream from load cells.')
        parser.add_argument("--input", help="Load cell serial numbers and inputs.", nargs='+')
	args = parser.parse_args()
        
        bridge_inputs = getBridgeInputs(args.input)
	#print set([v[0].getSerialNum() for v in bridge_inputs]); sys.exit(0)
	#q = [Queue.Queue(maxsize=100) for v in range(len(bridge_inputs))]
	q = [[] for v in range(len(bridge_inputs))]
	print '\n'.join(set([str(v[0].getSerialNum()) for v in bridge_inputs]))
	while bridge_inputs:
		print "\nserial\tbridge\tmean\tstd"
		for (i, (bridge,bridge_idx)) in enumerate(bridge_inputs):
			r = bridge.getBridgeValue(bridge_idx)
			#print i, r
			q[i].append(r)
			std, mean = 1e3*np.std(q[i]), np.mean(q[i])
			sig = "!!!!" if std > 2.0 or std < 0.01 else ""
			print "%d\t%d\t%0.1f\t%.1f\t%s" % (bridge.getSerialNum(), bridge_idx, mean, std, sig)
		time.sleep(0.01)
		time.sleep(0.1)
