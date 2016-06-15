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
import argparse, json
from os.path import *
from kitchen import *
from config.fridge_config import *
from db.db_handler import *
from data_stream.component_stream_recorded import *

def makeSnapshot(kitchen_id, event_id, event_time, datadir):
    # Get Kitchen and Snapshots dirs.
    kitchen_dir = join(datadir, "Kitchen%07d"%kitchen_id)
    snap_dir = join(kitchen_dir, "Snapshots")
    if not exists(snap_dir): os.mkdir(snap_dir)
    # Get event object.
    constraints = ["Event.kitchen_id=%d"%kitchen_id, "Event.id=%d"%event_id, 
                   "Event.segment_id=Segment.id"]
    event = handler.get(["Event", "Segment"], constraints=constraints)[0]
    # Get camera streams.
    if [v for v in os.listdir(kitchen_dir) if "LoadCell" in v]:
        fridge_config = FridgeConfig(FRIDGE_FULL_CONFIG)
    else:
        fridge_config = FridgeConfig(FRIDGE_STORAGE_CONFIG)
    fridge_stream = ComponentStreamRecorded(fridge_config, kitchen_dir)
    cams = fridge_stream.camera_streams.values()
    time_cam = cams[0]
    # Compute time.
    has_scale_data = len(fridge_stream.scale_streams) > 0
    seg_name = dateTimeToTimeString(timeStringToDateTime(event["Segment.time"]))
    s_idx = fridge_stream.getSegmentIndex(seg_name)
    begin_t = time_cam.getTime(s_idx, 0)
    dt = datetime.timedelta(seconds=1)
    if has_scale_data:
        begin_t = max(begin_t, timeStringToDateTime(event["Event.prev_stable_end_time"])-dt)
    t = begin_t + datetime.timedelta(seconds=event_time)
    # Insert into database??
    #handler.insert(["Snapshot"], {"event_id=%d"%event_id})
    # Write images.
    for (i, cam) in enumerate(cams):
        data = cam.getDataAtTime(s_idx, t)
        for im in [data, cv2.flip(cv2.transpose(data),0)]:
            fname = join(snap_dir, "Snapshot%06d-%d-%dx%d.png"%(event_id, i, im.shape[1], im.shape[0]))
            print fname
            cv2.imwrite(fname, im)

def init(datadir, service_config):
    global handler
    config = json.loads(open(service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"], config["db-host"])

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--data", help="Input data.", default=DATA)
    parser.add_argument("--service-config", help="Service config.", default=PROCESSING_CONFIG)
    parser.add_argument("--kitchen-id", help="Kitchen ID", type=int, required=True)
    parser.add_argument("--event-id", help="Event ID", type=int, required=True)
    parser.add_argument("--event-time", help="Event time", type=float, required=True)
    args = parser.parse_args()
    
    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"], config["db-host"])
    makeSnapshot(args.kitchen_id, args.event_id, args.event_time, args.data)
