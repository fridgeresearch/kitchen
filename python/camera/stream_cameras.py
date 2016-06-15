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

Program to stream live or recorded camera data and visualize the images.
"""
import sys, os, argparse
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_utils import *
from utils.general_utils import *
from utils.cv_utils import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Stream camera data.')
    parser.add_argument("--data", help="Input / output directories", nargs="+")
    parser.add_argument("--cameras", help="Cameras", nargs="+")
    parser.add_argument("--downscale", help="Downscale.", type=int, 
                        default=1 if "linux" in sys.platform else 8)
    args = parser.parse_args()
    
    checkStreamArgs(parser, args.data, args.cameras)
    record = False
    if args.cameras and args.data:
        streams = [CameraStreamLive(*v) for v in zip(args.cameras, args.data)]
        t = streams[0].getCurrentTime()
        [v.createWriter(t, fps=30.0) for v in streams]
        record = True
    elif args.cameras:
        streams = [CameraStreamLive(v) for v in args.cameras]
    else:
        streams = map(CameraStreamRecorded, args.data)
    vis_ims, vis_shape = [None for v in streams], None
    try:
        while streamsNotDone(streams):
            for (i, stream) in enumerate(streams):
                if not passStream(stream, streams):
                    data = stream.getCurrentData()
                    t = stream.getCurrentTime()
                    if record: stream.write(t, data)
                    vis_ims[i] = 1*data
                    if vis_shape==None: vis_shape = vis_ims[i].shape[:2]
                    stream.updateCurrent()
            vis_im = tileImages([cv2.resize(v, vis_shape[::-1]) if v!=None \
                                 else np.zeros(vis_shape) for v in vis_ims])
            cv2.imshow("vis", resize(vis_im, 1.0/args.downscale))
            ch = getKey(cv2.waitKey(1))
            if ch=='q':
                break
    except Exception as e:
        handleException("name", e)
    if record:
        for stream in streams:
            t = stream.getCurrentTime()
            stream.setWriterEndTimes(t)
            stream.closeWriters(t)

#print "Frame count =", cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)                                           
#print "Frame count =", cap.get(cv2.CAP_PROP_FRAME_COUNT)                                                 
#print "FPS =", cap.get(cv2.cv.CV_CAP_PROP_FPS)
