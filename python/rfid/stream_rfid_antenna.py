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

Program to stream live or recorded RFID antenna and visualize tag RSSI's.
"""
import sys, os, argparse
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_utils import *
from utils.general_utils import *
from utils.cv_utils import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Stream RFID data.')
    parser.add_argument("--data", help="Input directories", nargs="+")
    parser.add_argument("--antennas", help="antennas", nargs="+")
    parser.add_argument("--interface", help="interface", default="eth", choices=["eth", "usb"])
    parser.add_argument("--miny", help="Min y for plotting", type=float)
    parser.add_argument("--maxy", help="Max y for plotting", type=float)
    parser.add_argument("--power", help="power", type=int)
    parser.add_argument("--session", help="session")
    args = parser.parse_args()
    
    if (not args.data and not args.antennas) or (args.data and args.antennas):
        parser.print_help()
        print("Error: Must specify either data or antennas")
        sys.exit(89)
    
    if args.data:
        streams = map(RfidAntennaStreamRecorded, args.data)
    else:
        streams = [RfidAntennaStreamLive(args.interface.capitalize()+v) for v in args.antennas]
    if args.miny==None: args.miny = 70 if args.interface=="usb" else -80
    if args.maxy==None: args.maxy = 120 if args.interface=="usb" else -10
    plotters = [StreamingPlotter(args.miny, args.maxy, 10.0) for v in streams]
    epcs = set([])
    try:
        while streamsNotDone(streams):
            #epcs = set([])
            for (stream, plotter) in zip(streams, plotters):
                if not passStream(stream, streams):
                    for tag in stream.getCurrentData():
                        plotter.update(tag.time, tag.epc, tag.rssi)
                        epcs.add(tag.epc)
                    stream.updateCurrent()
            #print len(epcs)
            t = currentTime(streams)
            ims = [v.plot(t) for v in plotters]
            cv2.imshow("vis", tileImages(ims))
            ch = getKey(cv2.waitKey(100))
            if ch=='q':
                break
    except Exception as e:
        handleException("main", e)
    [v.release() for v in streams]
    
