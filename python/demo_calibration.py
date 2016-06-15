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
import sys, os, argparse, threading, select, cv2, logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from config.fridge_config import *
from extrinsics.extrinsic_calibration import *
from utils.general_utils import *
from utils.cv_utils import *
from data_stream.fridge_stream import *

def handleCharacter(ch, name):
    global record_tare, auto_tare
    if ch == 'q':
        logging.info("%s Quitting." % (name,))
        return 1
    elif ch == 'z': 
        record_tare = True
        logging.info("%s record_tare = %s." % (name, record_tare))
    elif ch == 't':
        auto_tare = not auto_tare
        logging.info("%s auto_tare = %s." % (name, auto_tare))
    return 0

def estimateObjectsInImages():
    name = inspect.stack()[0][3]
    global object_im_circles
    buff = 5
    while not quit_all:
        if not ims: time.sleep(1.0); continue
        transforms, markers = extrinsic_calibration.predict(ims)
        object_im_circles = [[] for v in range(len(ims))]
        scale_elements = [v[1] for v in sorted(fridge_config.scales.items())]
        for (element, (x, y, f)) in zip(scale_elements, force_vectors):
            if abs(f) > MAX_STABLE_FORCE:
                scale_section = [v for v in fridge_config.sections.values() \
                                     if element in [u for w in v.surfaces.values() \
                                                        for u in w.scales.values()]][0]
                object_in_world = np.array(list(element.planePointInWorld(x, y))+[1.0])
                cameras = sorted(fridge_config.cameras.keys())
                for i in range(len(ims)):
                    cam_section = [v for v in fridge_config.sections.values() \
                                       if cameras[i] in v.cameras.keys()][0]
                    if transforms[i] != None and scale_section==cam_section:
                        T_world_in_camera = transforms[i]
                        object_in_camera = T_world_in_camera.dot(object_in_world)
                        u, v = map(int, projectPoint(object_in_camera, CAMERA_CMAT))
                        if u>=buff and u<ims[i].shape[1]-buff and v>=buff and v<ims[i].shape[0]-buff:
                            object_im_circles[i].append((u,v,f))

def recordCamera():
    name = inspect.stack()[0][3]
    global ims, record_tare, writer
    cv2.namedWindow("vis")
    while not quit_all:
        if [1 for t in threads if not t.isAlive()]: break
        ims = [v[1].getCurrentData() for v in sorted(fridge_stream.camera_streams.items())]
        [cv2.circle(ims[i], (u,v), int(abs(f)/10), thickness=5, color=[0,0,255] if f>0 else [255,0,0])\
         for i in range(len(ims)) for (u, v, f) in object_im_circles[i]]
        vis = tileImages([resize(v, 1.0/args.downscale) for v in ims])
        cv2.imshow("vis", vis)
        if writer: writer.write(vis)
        if handleCharacter(getKey(cv2.waitKey(1)), name): break
        if scale != None and camera != None:
            while not quit_all and \
                  datetimeToUnix(camera.getCurrentTime()) > datetimeToUnix(scale.getCurrentTime())+0.1:
                time.sleep(0.01)
        try:
            [v.updateCurrent() for v in fridge_stream.camera_streams.values()]
        except Exception as e:
            logging.info("%s cannot updateCurrent()." % (name,))
            break

def recordScales():
    name = inspect.stack()[0][3]
    global record_tare, force_vectors
    tare, forces_q = None, []
    while not quit_all and force_vectors != None:
        t_str = scale.getCurrentTime(); t = datetimeToUnix(t_str)
        forces = np.array([v.getCurrentLoadCellForces() \
                           for v in fridge_stream.scale_streams.values()]).reshape(-1)
        forces_q = [v for v in forces_q+[(t,forces)] if t-v[0] < 3.0]
        max_diff = np.max(np.abs(forces - [v[1] for v in forces_q]))
        if max_diff < MAX_STABLE_FORCE:
            tare = [v[1].getCurrentData() for v in sorted(fridge_stream.scale_streams.items())]
        if tare != None:
            force_vectors = [v[0][1].getCurrentForceVector(v[1]) \
                             for v in zip(sorted(fridge_stream.scale_streams.items()), tare)]
        if scale != None and camera != None:
            while not quit_all and \
                  datetimeToUnix(scale.getCurrentTime()) > datetimeToUnix(camera.getCurrentTime())+0.1:
                time.sleep(0.01)
        try:
            [v.updateCurrent() for v in fridge_stream.scale_streams.values()]
        except Exception as e:
            logging.info("%s cannot updateCurrent()." % (name,))
            break
        time.sleep(0.01)

def handleKeyPress():
    name = inspect.stack()[0][3]
    global record_tare
    while not quit_all:
        rlist, ch = select.select([sys.stdin], [], [], 0.1)[0], ''
        if rlist:
            line = sys.stdin.readline()
            ch = line[0] if len(line) else None
        else:
            continue
        if handleCharacter(ch, name): break

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='SmartFridge recording.')
    parser.add_argument("--data", help="Input data directory.")
    parser.add_argument("--downscale", help="Downscale.", type=int, default=4)
    parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG)
    parser.add_argument("--model", help="ExtrinsicCalibration model.", default=EXTRINSICS_MODEL)
    parser.add_argument("--auto-tare", help="Auto tare.", action="store_true")
    parser.add_argument("--video", help="Output video file.")
    args = parser.parse_args()

    configureLogging()

    # Calibrations
    fridge_config = FridgeConfig(args.config)
    extrinsic_calibration = ExtrinsicCalibration(fridge_config, fname=args.model)
    
    # Fridge stream
    fridge_stream = FridgeStream(fridge_config, args.data)
    camera, scale = [v[0] if len(v) else None for v in \
                     [fridge_stream.camera_streams.values(), fridge_stream.scale_streams.values()]]

    # Cv2VideoWriter
    writer = Cv2VideoWriter(args.video) if args.video else None
    
    # Thread creation and collection.
    quit_all, record_tare, force_vectors = False, False, []
    auto_tare = True if args.auto_tare else False
    ims, object_im_circles = [], [[] for v in range(len(fridge_config.cameras))]
    threads = [threading.Thread(target=v) for v in [recordScales, handleKeyPress, estimateObjectsInImages]]
    for t in threads:
        t.daemon = True
        t.start()
    recordCamera()
    quit_all = True
    [t.join() for t in threads]
    if writer: writer.release()
