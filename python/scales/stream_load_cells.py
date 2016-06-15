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

Program to stream live or recorded load cells and visualize readings.
"""
import sys, os, argparse
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_utils import *
from utils.general_utils import *
from utils.cv_utils import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Stream load cell data.')
    parser.add_argument("--data", help="Input / output directories", nargs="+")
    parser.add_argument("--load-cells", help="Load cells", nargs="+")
    parser.add_argument("--miny", help="Min y for plotting", type=float, default=-1.0)
    parser.add_argument("--maxy", help="Max y for plotting", type=float, default=1.0)
    args = parser.parse_args()
    
    checkStreamArgs(parser, args.data, args.load_cells)
    record = False
    if args.load_cells and args.data:
        streams = [LoadCellStreamLive(*v) for v in zip(args.load_cells, args.data)]
        t = streams[0].getCurrentTime()
        [v.createWriter(t) for v in streams]
        record = True
    elif args.load_cells:
        streams = [LoadCellStreamLive(v) for v in args.load_cells]
    else:
        streams = map(LoadCellStreamRecorded, args.data)        
    names = args.load_cells if args.load_cells else args.data
    plotter = StreamingPlotter(miny=args.miny, maxy=args.maxy)
    try:
        it = 0
        while streamsNotDone(streams):
            for (stream, name) in zip(streams, names):
                if not passStream(stream, streams):
                    data = stream.getCurrentData()
                    t = stream.getCurrentTime()
                    if record: stream.write(t, "%f\n"%data)
                    plotter.update(t, name, data)
                    stream.updateCurrent()
            if True or it%10 == 0:
                cv2.imshow("vis", plotter.plot(t))
                ch = getKey(cv2.waitKey(1))
                if ch=='q':
                    break
            it += 1
    except Exception as e:
        handleException("name", e)
    #cv2.imshow("vis", plotter.plot(t))
    #ch = getKey(cv2.waitKey(0))
    if record:
        for stream in streams:
            t = stream.getCurrentTime()
            stream.setWriterEndTimes(t)
            stream.release()
