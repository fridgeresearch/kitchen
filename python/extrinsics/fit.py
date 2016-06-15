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

Program that allows user to fit an ExtrinsicCalibration to selected image sets.
"""
import sys, os, argparse, cv2
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.fridge_config import *
from extrinsics.extrinsic_calibration import *
from utils.general_utils import *
from utils.cv_utils import *
from data_stream.fridge_stream import *

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Evaluate calibration.')
    parser.add_argument("--input", help="Input data.", default=EXTRINSICS_RECORDING)
    parser.add_argument("--output", help="Output directory.", default=EXTRINSICS_MODEL)
    parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG)
    parser.add_argument("--downscale", help="Downscale factor.", type=int, default=2)
    parser.add_argument("--video", help="Output video file.")
    args = parser.parse_args()
    
    fridge_config = FridgeConfig(args.config)
    fridge_stream = FridgeStream(fridge_config, args.input, ignore_scales=True)
    cam_names, cams = zip(*sorted(fridge_stream.camera_streams.items()))
    calibration = ExtrinsicCalibration(fridge_config, \
                                       fname=args.output if os.path.exists(args.output) else None)
    s_idx, d_idx, ch, wait = 0, 0, 'start', 0
    writer = Cv2VideoWriter(args.video) if args.video else None
    while True:
        if ch != '': wait = 0
        if ch.lower() in ['j', 'k', '', 'start']:
            if ch=='start':
                step = 0
            else:
                step = (10 if ch.isupper() or ch=='' else 1) * (-1 if ch.lower()=='j' else 1)
            d_idx = min(cams[0].numSegmentData(s_idx)-1, max(0, d_idx+step))
            if d_idx==cams[0].numSegmentData(s_idx)-1:
                if s_idx < cams[0].numSegments()-1:
                    s_idx, d_idx = s_idx+1, 0
                else:
                    wait = 0
            time = cams[0].getTime(s_idx, d_idx) # just to make sure initialized
            ims = [v.getData(s_idx, d_idx) for v in cams]
            print("Segment=%d, Frame=%d" % (s_idx, d_idx))
        if ch in ['c', '']:
            calibration.update(time, ims)
            calibration.save(args.output)
        if ch=='!':
            calibration.delete(time)
            calibration.save(args.output)
        if ch=='*':
            wait = 10
        if ch=='q':
            break
        transforms, markers = calibration.getData(cams[0].getTime(s_idx, d_idx))
        vis = []
        calib_ids = map(int, fridge_config.markers.keys())
        for (i, im) in enumerate(ims):
            im = drawWorld(im, fridge_config, cam_names[i], transforms[i])
            [v.draw(im, (255,0,0)) for v in markers[i]]
            [v.draw(im, (0,0,255)) for v in markers[i] if v.id in calib_ids]
            vis.append(im)
        vis = resize(tileImages(vis), 1.0/args.downscale)
        cv2.imshow("vis", vis)
        if writer: writer.write(vis)
        ch = getKey(cv2.waitKey(wait))
    if writer: writer.release()
