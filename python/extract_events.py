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

Program to extract events from fridge stream and update the database accordingly.
Iterates over kitchens. For each kitchen, iterates over segments. For each
unprocessed segment that is not too new, iterates over surfaces.
For each surface, extract all events.

Event extraction works by creating an event for each time when a scale is
unstable and then stabilizes in a different state (different load cell readings).
"""
import sys, os, argparse, logging, inspect, json, numpy as np, matplotlib.pyplot as plt
from os.path import *
from kitchen import *
from utils.general_utils import *
from utils.cv_utils import *
from utils.logging_utils import *
from db.db_handler import *
from config.fridge_config import *
from rfid.rfid_tag_read import *
from data_stream.stream_utils import *
from scales.scale_utils import *
from utils.general_utils import *

conv = lambda x: dateTimeToTimeString(x) if x!=None else None

def extractAndInsertEvents(handler, kitchen_id, seg_id, s_idx, seg_name, fridge_stream):
    """Extracts events from all surfaces.
    
    Iterates over surfaces. For each surface, calls func to extract events.
        Then inserts these events in time-sorted order.
    
    Args:
        handler: Database handler.
        kitchen_id: Kitchen ID.
        seg_id: Segment ID.
        s_idx: Segment index.
        fridge_stream: Fridge stream.

    Returns:
        Dictionary returned from database of all events for this segment.
    """
    events = []
    # Compute whether or not we have scale data
    has_scale_data = fridge_stream.model.surfaces
    if has_scale_data:
        for (surface_name, surface) in fridge_stream.model.surfaces.items():
            scale_name, scale_element = surface.scales.items()[0]
            scale_stream = fridge_stream.scale_streams[scale_name]
            has_scale_data = has_scale_data and scale_stream.numSegmentData(s_idx)
    # If scale data, extract per-surface.
    if has_scale_data:
        for (surface_name, surface) in fridge_stream.model.surfaces.items():
            events += extractSurfaceEvents(kitchen_id, seg_id, s_idx, \
                                           fridge_stream, surface, surface_name)
    # Otherwise just extract one event for the segment.
    else:
        events = [extractEvent(kitchen_id, seg_id, s_idx, fridge_stream)]
        
    handler.insertMany("Event", sorted(events, key=lambda x: x["time"]))
    return handler.getEvents(kitchen_id=kitchen_id, segment_id=seg_id)

def extractEvent(kitchen_id, seg_id, s_idx, fridge_stream):
    """Extracts event for the segment.
    
    For surface-less setups, simply extracts an event for the segment.
    
    Args:
        handler: Database handler.
        kitchen_id: Kitchen ID.
        seg_id: Segment ID.
        s_idx: Segment index.
        fridge_stream: Fridge stream.

    Returns:
        Dictionary returned from database of event for this segment.
    """
    name = inspect.stack()[0][3]
    t = fridge_stream.seg_names[s_idx]
    prev_times = [w.getTime(s_idx, 0) for v in fridge_stream.streams.values() \
                  for w in v.values() if w.numSegmentData(s_idx) > 1]
    if prev_times:
        prev_start_t = min([w.getTime(s_idx, 0) for v in fridge_stream.streams.values() \
                            for w in v.values() if w.numSegmentData(s_idx) > 1])
        prev_end_t = prev_start_t + datetime.timedelta(seconds=1)
        end_t = max([w.getTime(s_idx, w.numSegmentData(s_idx)-1) for v in fridge_stream.streams.values() \
                     for w in v.values() if w.numSegmentData(s_idx) > 1])
        start_t = end_t - datetime.timedelta(seconds=1)
    else:
        prev_start_t, prev_end_t, end_t, start_t = None, None, None, None
    logging.info("%s Inserting (%s)" % (name, t))
    return {"time":t, "kitchen_id":kitchen_id, "segment_id":seg_id, "processed":0,
            "prev_stable_start_time":conv(prev_start_t), "prev_stable_end_time":conv(prev_end_t),
            "stable_start_time":conv(start_t), "stable_end_time":conv(end_t)}

def extractSurfaceEvents(kitchen_id, seg_id, s_idx, \
                         fridge_stream, surface, surface_name):
    """Extracts events and inserts them into the database.
    
    Analyzes scale's load cells' forces to identify stable and unstable regions.
        Inserts event for each stable region (after the first). When inserting,
        finds tare from previous stable then uses to get force vector.

    Args:
        kitchen_id: Kitchen ID.
        seg_id: Segment ID.
        s_idx: Segment index.
        fridge_stream: Fridge stream.
        surface: Surface.
        surface_name: Surface name.

    Returns:
        List of Event dictionaries.
    """
    name = inspect.stack()[0][3]
    scale_name, scale_element = surface.scales.items()[0]
    scale_stream = fridge_stream.scale_streams[scale_name]
    event_times = extractEventTimes(scale_stream, s_idx)
    events = []
    for (prev_start_t, prev_end_t, prev_t, start_t, end_t, t) in event_times:
        tare = scale_stream.getDataAtTime(s_idx, prev_t)
        x, y, f = scale_stream.getForceVectorAtTime(s_idx, t, tare)
        if abs(f) < MAX_STABLE_FORCE: continue # non-events
        x, y, z = scale_element.planePointInWorld(x, y)
        logging.info("%s Inserting (%s %d %s)" % (name, surface_name, f, t))
        events.append({"time":conv(t), "kitchen_id":kitchen_id,
                       "segment_id":seg_id, "surface":surface_name,
                       "prev_stable_start_time":conv(prev_start_t),
                       "prev_stable_end_time":conv(prev_end_t),
                       "stable_start_time":conv(start_t),
                       "stable_end_time":conv(end_t),
                       "tare_time":conv(prev_t),
                       "x":x, "y":y, "z":z, "event_force":f, "processed":0})
    return events

def extractAndInsertTags(handler, fridge_stream, s_idx):
    """Extracts and returns tag data; inserts new tags into database.
    
    Args:
        handler: Database handler.
        s_idx: Segment index.
        fridge_stream: Fridge stream.

    Returns:
        Dictionary from tag_id to per-antenna RSSI time series.
    """
    name = inspect.stack()[0][3]
    # Find dict from epc to data.
    existing_epcs = set([v["Tag.epc"] for v in handler.get(["Tag"])])
    epc_to_data = {}
    for (antenna, stream) in fridge_stream.rfid_antenna_streams.items():
        for d_idx in range(stream.numSegmentData(s_idx)):
            for tag in stream.getData(s_idx, d_idx):
                if tag.epc not in epc_to_data:
                    epc_to_data[tag.epc] = {}
                if antenna not in epc_to_data[tag.epc]:
                    epc_to_data[tag.epc][antenna] = []
                #ut = datetimeToUnix(tag.time)
                #epc_to_data[tag.epc][antenna].append((ut, tag.rssi))
                epc_to_data[tag.epc][antenna].append((tag.time_str, tag.rssi))
    # Insert new tags.
    new_tags = [{"epc":v} for v in set(epc_to_data.keys())-existing_epcs]
    for tag in new_tags:
        logging.info("%s Inserting %s" % (name, tag["epc"]))
    handler.insertMany("Tag", new_tags)
    # Return dict from id to data.
    epc_to_id = dict([(v["Tag.epc"], v["Tag.id"]) for v in handler.get(["Tag"])])
    id_to_data = {}
    for (epc, data) in epc_to_data.items():
        id_to_data[epc_to_id[epc]] = data
    return id_to_data

def insertTagSegmentRead(handler, tag_id, seg_id, data, stable_start, stable_end):
    """Inerts tag segment read.
    
    Args:
        handler: Database handler.
        tag_id: Tag ID.
        seg_id: Segment ID.
        data: Tag segment data (per-antenna RSSI time series)
    """
    name = inspect.stack()[0][3]
    score = RfidPresenceClassifier().eval(data, stable_start, stable_end)
    #logging.info("%s Inserting (%s, %.1f, %s, %s)" % \
    #             (name, tag_id, score, stable_start, stable_end))
    tsr = {"tag_id":tag_id, "segment_id":seg_id, "presence_score":score}
    handler.insert("TagSegmentRead", tsr)
    #x, y = zip(*data.values()[0])
    #plt.plot(x, y)
    #plt.show()

def insertTagEventRead(handler, event_id, tag_id, data, stable_start, stable_end):
    """Insert tag event read.
    
    Args:
        handler: Database handler.
        event_id: Event ID.
        tag_id: Tag ID.
        seg_data: Tag segment data (per-antenna RSSI time series)
    """
    name = inspect.stack()[0][3]
    ascore = RfidArrivalClassifier().eval(data, stable_start, stable_end)
    rscore = RfidRemovalClassifier().eval(data, stable_start, stable_end)
    ter = {"tag_id":tag_id, "event_id":event_id, "arrival_score":ascore, "removal_score":rscore}
    handler.insert("TagEventRead", ter)

def extractAndInsertBeacons(handler, fridge_stream, s_idx):
    """Extracts and returns beacon data; inserts new beacons into database.
    
    Args:
        handler: Database handler.
        s_idx: Segment index.
        fridge_stream: Fridge stream.

    Returns:
        Dictionary from beacon_id to RSSI time series.
    """
    name = inspect.stack()[0][3]
    # Find dict from addr to data.
    existing_addrs = set([v["Beacon.address"] for v in handler.get(["Beacon"])])
    addr_to_data = {}
    for (ble, stream) in fridge_stream.ble_streams.items():
        for d_idx in range(stream.numSegmentData(s_idx)):
            for beacon in stream.getData(s_idx, d_idx):
                if beacon.addr not in addr_to_data:
                    addr_to_data[beacon.addr] = []
                addr_to_data[beacon.addr].append((beacon.time_str, beacon.rssi))
    # Insert new beacons.
    new_beacons = [{"address":v} for v in set(addr_to_data.keys())-existing_addrs]
    #for beacon in new_beacons:
    #    logging.info("%s Inserting %s" % (name, beacon["addr"]))
    handler.insertMany("Beacon", new_beacons)
    # Return dict from id to data.
    addr_to_id = dict([(v["Beacon.address"], v["Beacon.id"]) for v in handler.get(["Beacon"])])
    id_to_data = {}
    for (addr, data) in addr_to_data.items():
        id_to_data[addr_to_id[addr]] = data
    return id_to_data

def insertBeaconSegmentRead(handler, beacon_id, seg_id, data, stable_start, stable_end):
    """Inerts beacon segment read.
    
    Args:
        handler: Database handler.
        beacon_id: Beacon ID.
        seg_id: Segment ID.
        data: Beacon segment data (per-antenna RSSI time series)
    """
    name = inspect.stack()[0][3]
    score = BeaconPresenceClassifier().eval(data, stable_start, stable_end)
    #logging.info("%s Inserting (%s, %.1f, %s, %s)" % \
    #             (name, beacon_id, score, stable_start, stable_end))
    bsr = {"beacon_id":beacon_id, "segment_id":seg_id, "presence_score":score}
    handler.insert("BeaconSegmentRead", bsr)
    #x, y = zip(*data.values()[0])
    #plt.plot(x, y)
    #plt.show()

def insertBeaconEventRead(handler, event_id, beacon_id, data, 
                          prev_stable_start, prev_stable_end, stable_start, stable_end):
    """Insert beacon event read.
    
    Args:
        handler: Database handler.
        event_id: Event ID.
        beacon_id: Beacon ID.
        seg_data: Beacon segment data (per-antenna RSSI time series)
    """
    name = inspect.stack()[0][3]
    ascore = BeaconArrivalClassifier().eval(data, prev_stable_start, prev_stable_end, stable_start, stable_end)
    rscore = BeaconRemovalClassifier().eval(data, prev_stable_start, prev_stable_end, stable_start, stable_end)
    ter = {"beacon_id":beacon_id, "event_id":event_id, "arrival_score":ascore, "removal_score":rscore}
    handler.insert("BeaconEventRead", ter)

def processFridgeStream(kitchen_id, fridge_stream, handler):
    name = inspect.stack()[0][3]
    # Process each segment in the FridgeStream.
    for (i, seg_name) in enumerate(fridge_stream.seg_names):
        s_idx = fridge_stream.getSegmentIndex(seg_name)
        t = timeStringToDateTime(seg_name)
        dt = (datetime.datetime.utcnow()-t).total_seconds()
        t_str = dateTimeToTimeString(t)
        constraints = ["kitchen_id=%d"%kitchen_id, "time='%s'"%t_str]
        segments = handler.get(["Segment"], constraints=constraints)
        # Only process if the segment is unprocessed and is not too new.
        if not segments and dt > 90:
            logging.info("%s Processing kitchen=%d segment=%s." % (name, kitchen_id, seg_name))
            # Insert Segment.
            handler.insert("Segment", {"kitchen_id":kitchen_id, "time":t_str})
            seg_id = handler.lastRowId()
            # Extract and insert events.
            events = extractAndInsertEvents(handler, kitchen_id, seg_id, s_idx, seg_name, fridge_stream)
            if not events: 
                handler.commit()
                continue
            stable_start = max([v["Event.stable_start_time"] for v in events])
            stable_end = max([v["Event.stable_end_time"] for v in events])
            # Extract and insert tags.
            tags = extractAndInsertTags(handler, fridge_stream, s_idx)
            for (tag_id, tag_data) in tags.items():
                # TagSegmentRead
                insertTagSegmentRead(handler, seg_id, tag_id, tag_data, stable_start, stable_end)
                # TagEventRead
                for event in events:
                    event_stable_start = event["Event.stable_start_time"]
                    event_stable_end = event["Event.stable_end_time"]
                    insertTagEventRead(handler, event["Event.id"], tag_id, tag_data, \
                                       event_stable_start, event_stable_end)
            # Extract and insert beacons.
            beacons = extractAndInsertBeacons(handler, fridge_stream, s_idx)
            for (beacon_id, beacon_data) in beacons.items():
                # BeaconSegmentRead
                insertBeaconSegmentRead(handler, seg_id, beacon_id, beacon_data, stable_start, stable_end)
                # BeaconEventRead
                for event in events:
                    event_prev_stable_start = event["Event.prev_stable_start_time"]
                    event_prev_stable_end = event["Event.prev_stable_end_time"]
                    event_stable_start = event["Event.stable_start_time"]
                    event_stable_end = event["Event.stable_end_time"]
                    insertBeaconEventRead(handler, event["Event.id"], beacon_id, beacon_data, \
                                          event_prev_stable_start, event_prev_stable_end,
                                          event_stable_start, event_stable_end)
            handler.commit()
            #break

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--data", help="Input data.", default=DATA)
    parser.add_argument("--service-config", help="Service config.", default=PROCESSING_CONFIG)
    #parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG) # TODO(jake): hack
    args = parser.parse_args()
    
    configureLogging()
    #fridge_config = FridgeConfig(args.config)
    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"], config["db-host"])
    
    # Process each kitchen.
    for row in handler.get(["Kitchen"]):
        kitchen_id = row["Kitchen.id"]
        kitchen_name = row["Kitchen.name"]
        kitchen_dir = os.path.join(args.data, "Kitchen%07d"%kitchen_id)
        if not os.path.exists(kitchen_dir): continue
        if [v for v in os.listdir(kitchen_dir) if "LoadCell" in v]:
            fridge_config = FridgeConfig(FRIDGE_FULL_CONFIG)
        else:
            fridge_config = FridgeConfig(FRIDGE_STORAGE_CONFIG)
        fridge_stream = ComponentStreamRecorded(fridge_config, kitchen_dir)
        processFridgeStream(kitchen_id, fridge_stream, handler)
    handler.commit()
