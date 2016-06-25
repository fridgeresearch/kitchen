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
import sys, os, argparse, logging, inspect, json, numpy as np
from os.path import *
from kitchen import *
from utils.general_utils import *
from utils.logging_utils import *
from utils.cv_utils import *
from db.db_handler import *
from config.fridge_config import *
from data_stream.stream_utils import *
from extrinsics.extrinsic_calibration import *

def makeEventMedia(event, fridge_stream, handler, events_dir):
    name = inspect.stack()[0][3]
    #logging.info("%s Processing fridge=%d event=%s." % (name, fridge_id, event["Event.id"]))
    # Create event directories.
    event_stem = join(events_dir, "Event%06d"%event["Event.id"])
    event_video = event_stem+".mp4"
    if os.path.exists(event_video): return
    logging.info("%s Creating video %s." % (name, event_video))
    # Get the beginning and ending indices for the video.
    segs = handler.get(["Segment"], constraints=["id=%d"%event["Event.segment_id"]])
    seg_time = segs[0]["Segment.time"]
    # Convert from / to time string because db string format different.
    seg_name = dateTimeToTimeString(timeStringToDateTime(seg_time))
    s_idx = fridge_stream.getSegmentIndex(seg_name)
    cams = fridge_stream.camera_streams.values()
    time_cam = cams[0]
    if event["Event.surface"]: # has scale data
        # Compute the tare.
        scale_name, scale_element = fridge_stream.model.surfaces[event["Event.surface"]].scales.items()[0]
        scale_stream = fridge_stream.scale_streams[scale_name]
        tare = scale_stream.getDataAtTime(s_idx, timeStringToDateTime(event["Event.tare_time"]))
        # Get starting and ending times.
        t0, t1 = [timeStringToDateTime(event["Event.%s"%v]) \
                  for v in ['prev_stable_end_time','stable_start_time']]
    else:
        # Get starting and ending times.
        t0 = time_cam.getTime(s_idx, 0)
        d_idx = time_cam.numSegmentData(s_idx)
        t1 = time_cam.getTime(s_idx, d_idx-1)
    begin_t, end_t = t0-datetime.timedelta(seconds=1), t1+datetime.timedelta(seconds=1)
    begin_i, end_i = [time_cam.nearestIndexToTime(s_idx, t) for t in [begin_t,end_t]]
    # Create video (of tiled images).
    fps = (end_i-begin_i)/(end_t-begin_t).total_seconds()
    writer, buff = Cv2VideoWriter(event_video, fps=fps), 5
    for d_idx in range(begin_i, end_i+1):
        # Get object position in world.
        t = time_cam.getTime(s_idx, d_idx)
        if event["Event.surface"]:
            x, y, f = scale_stream.getForceVectorAtTime(s_idx, t, tare)
            x, y, z = scale_element.planePointInWorld(x, y)
            #color = [0,255,0] if f>0 else [0,0,255]
            color = [0,255,0] if event["Event.event_force"]>0 else [0,0,255]
        else:
            color = [255,255,255]
        camera_names, cameras = zip(*sorted(fridge_stream.camera_streams.items()))
        ims = [v.getDataAtTime(s_idx, t) for v in cameras]
        if False and abs(f) > MAX_STABLE_FORCE: # TODO(jake): fix when calibrated
            object_in_world = np.array([x,y,z,1.0])
            transforms, markers = extrinsic_calibration.predict(ims)
        else:
            transforms, object_in_world = [None]*len(ims), None
        # Tile images.
        for i in range(len(ims)):
            vs = fridge_stream.model.cameras[camera_names[i]].visible_surfaces
            if event["Event.surface"] in vs:
                if t0 <= t <= t1:
                    sz = (ims[i].shape[1]-1, ims[i].shape[0]-1)
                    cv2.rectangle(ims[i], (0,0), sz, color, 20)
                if object_in_world!=None and transforms[i]!=None:
                    T_world_in_camera = transforms[i]
                    object_in_camera = T_world_in_camera.dot(object_in_world)
                    u, v = map(int, projectPoint(object_in_camera, CAMERA_CMAT))
                    if u>=buff and u<ims[i].shape[1]-buff and v>=buff and v<ims[i].shape[0]-buff:
                        cv2.circle(ims[i], (u,v), int(abs(f)/10), thickness=5, color=color)
        vis = tileImages(ims)
        sf = 960.0 / vis.shape[1]
        vis = resize(vis, sf)
        writer.write(vis)
#        cv2.imshow("vis", vis)
        if getKey(cv2.waitKey(1))=='q': sys.exit(0)
    writer.close()
    [v.uninitAll() for v in cams] # free up mem

def processFridgeStream(kitchen_id, fridge_stream, handler):
    name = inspect.stack()[0][3]
    # Create Events and Segments directories if not yet created.
    events_dir = join(fridge_stream.in_dir, "Events")
    if not os.path.exists(events_dir): os.makedirs(events_dir)
    # Make media for all events.
    events = handler.getEvents(kitchen_id=kitchen_id)
    [makeEventMedia(v, fridge_stream, handler, events_dir) for v in events if v["Event.segment_id"]]

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--data", help="Input data.", default=DATA)
    #parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG) # TODO(jake): hack
    parser.add_argument("--service-config", help="Service config.", default=PROCESSING_CONFIG)
    parser.add_argument("--model", help="ExtrinsicCalibration model.", default=EXTRINSICS_MODEL)
    args = parser.parse_args()

    configureLogging()
    #fridge_config = FridgeConfig(args.config)
    #extrinsic_calibration = ExtrinsicCalibration(fridge_config, fname=args.model)
    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"], config["db-host"])
    
    # Process each kitchen.
    for row in handler.get(["Kitchen"]):
        kitchen_id = row["Kitchen.id"]
        kitchen_dir = os.path.join(args.data, "Kitchen%07d"%kitchen_id)
        if not os.path.exists(kitchen_dir): continue
        if [v for v in os.listdir(kitchen_dir) if "LoadCell" in v]:
            fridge_config = FridgeConfig(FRIDGE_FULL_CONFIG)
        else:
            fridge_config = FridgeConfig(FRIDGE_STORAGE_CONFIG)
        fridge_stream = ComponentStreamRecorded(fridge_config, kitchen_dir)
        processFridgeStream(kitchen_id, fridge_stream, handler)
