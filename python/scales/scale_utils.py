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

Module that provides load cell functionality.
"""
import sys, os, numpy as np
from os.path import *
from dateutil.parser import parse
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.general_utils import *

import matplotlib.pyplot as plt

def extractEventTimes(scale_stream, s_idx):
    inds = range(scale_stream.numSegmentData(s_idx))
    times = [scale_stream.getTime(s_idx, v) for v in inds]
    unix_times = map(datetimeToUnix, times)
    # Get load cell forces \in R^{time \times 3} and summed forces \in R^time.
    # Note that these are not tarred but ok since we're only concerned with differences.
    lc_forces = [scale_stream.getLoadCellForces(s_idx, v, warn=False) for v in inds]
    s_forces = np.sum(lc_forces, axis=1)
    # Compute windowed differences, take windowed max, and then find where stable.
    diffs = timeWindowedMaxDiff(s_forces, unix_times, 0.25)
    max_diffs = timeWindowedMax(diffs, unix_times, 0.5)
    stable = [v<MAX_STABLE_FORCE for v in max_diffs]
    stable[0], stable[-1] = True, True # TODO(jake): remove
    """
    plt.clf()
    plt.plot(unix_times, s_forces)
    plt.xlabel('time'); plt.ylabel('weight')
    #plt.show()
    plt.savefig("weight.png")
    print max_diffs
    print scale_stream.seg_names[s_idx]
    print "\t", scale_stream.load_cell_names
    """
    if not stable[0]:
        raise Exception("Unstable scale stream start for %s"%scale_stream.seg_names[s_idx])
    if not stable[-1]:
        raise Exception("Unstable scale stream end for %s"%scale_stream.seg_names[s_idx])
    # Find times when change to / from stable.
    starts = [i for (i,v) in enumerate(stable) if not i or (v and not stable[i-1])]
    ends = [i for (i,v) in enumerate(stable) if i==len(stable)-1 or (v and not stable[i+1])]
    stable_regions = [[times[w] for w in v] for v in zip(starts, ends)]
    # Get center points of stable regions.
    centers = [t0 + (t1-t0)/2 for (t0, t1) in stable_regions]
    # Return list of 6-tuples:
    # (prev stable start time, prev stable end time, prev time,
    #  stable start time, stable end time, time).
    return [(v[0][0],v[0][1], v[1], v[2][0], v[2][1], v[3]) for v in \
            zip(stable_regions, centers, stable_regions[1:], centers[1:])]
