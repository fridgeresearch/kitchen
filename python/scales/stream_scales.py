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

Program to stream live or recorded scales and visualize readings.
"""
import sys, os, argparse, time
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_utils import *
from utils.general_utils import *
from utils.cv_utils import *

class ScaleVisualization:
    def __init__(self, width=0.254, height=0.33, canvas_size=None):
        self.width, self.height = width, height
        if canvas_size==None:
            canvas_size = tuple([int(2000*v) for v in [self.height, self.width]])
        self.canvas_size = canvas_size
        self.colors = {}
    def update(self, name, x, y, F, im=None):
        if im==None: im = np.ones(self.canvas_size+(3,), dtype=np.uint8)*255
        if name not in self.colors:
            self.colors[name]  = np.random.randint(0,255,3)
        if F > 10:
            pt = tuple(map(int, ((x+self.width/2)/self.width*im.shape[1], \
                                 (y+self.height/2)/self.height*im.shape[0])))
                                 #y/self.height*im.shape[0])))
            cv2.circle(im, pt, int(F/10), thickness=5, color=self.colors[name])
        return im

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Stream scale data.')
    parser.add_argument("--data", help="Input / output directories", nargs="+")
    parser.add_argument("--scales", help="Scales", nargs="+")
    parser.add_argument("--miny", help="Min y for plotting", type=float, default=-500.0)
    parser.add_argument("--maxy", help="Max y for plotting", type=float, default=500.0)
    parser.add_argument("--vis", help="Visualize.", action="store_true")
    args = parser.parse_args()
    
    checkStreamArgs(parser, args.data, args.scales)
    record = False
    if args.scales and args.data:
        streams = [ScaleStreamLive(*v) for v in zip(args.scales, args.data)]
        t = streams[0].getCurrentTime()
        [v.createWriter(t) for v in streams]
        record = True
    elif args.scales:
        streams = [ScaleStreamLive(v) for v in args.scales]
    else:
        streams = [ScaleStreamRecorded(*v) for v in zip(args.data, args.scales)]
    names = args.scales if args.scales else args.data
    if args.vis:
        #plotter = StreamingPlotter(miny=args.miny, maxy=args.maxy)
        plotter = ScaleVisualization()
        tares = dict([(v,None) for v in names])
    try:
        while streamsNotDone(streams):
            im = None
            for (stream, name) in zip(streams, names):
                if not passStream(stream, streams):
                    data = stream.getCurrentData()
                    t = stream.getCurrentTime()
                    if record: stream.write(t, ["%f\n"%v for v in data])
                    if args.vis:
                        if tares[name]==None: tares[name] = np.array(data)
                        #x, y, F = stream.getCurrentForceVector(tares[name])
                        y, x, F = stream.getCurrentForceVector(tares[name])
                        #y, x, F = cal.predict(stream.getCurrentData()-tares[name])
                        #plotter.update(stream.getCurrentTime(), name, F)
                        im = plotter.update(name, x, y, F, im)
                    stream.updateCurrent()
            cv2.imshow("vis", im) if args.vis else cv2.imshow("vis", np.zeros((480,640)))
            ch = getKey(cv2.waitKey(1))
            if ch=='q':
                break
            time.sleep(0.1)
    except Exception as e:
        handleException("name", e)
    if record:
        for stream in streams:
            t = stream.getCurrentTime()
            stream.setWriterEndTimes(t)
            stream.closeWriters(t)
