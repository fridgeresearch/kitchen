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

Program to stream (and possibly record) live or recorded data from kitchen.
Works by spawning sensor-specific streaming threads based on the 
specified FridgeConfig's recording_streams attributes.
Each streaming thread constantly puts data onto the data queue.
The writeData() function gets this data from the queue.
Record events are registered through user input or specific environment
changes (eg, when lights come ON). In such cases, writeData()
writes data to disk. User input is received through the
image window or the terminal and handled by handleKeyPress().
"""
from kitchen import *
import argparse, sys, os, time, inspect, logging, threading, cv2, Queue, json, socket, requests
from os.path import *
from utils.general_utils import *
from utils.cv_utils import *
from utils.logging_utils import *
from config.fridge_config import *
from audio.audio_writer import *
from data_stream.stream_utils import *

def handleCharacter(ch, time_str, caller_name, config):
    """Handles character.
    
    Handles character. Options: q (quit)
    
    Args:
        ch: Character.
        time_str: Time string.
        caller_name: Calling function's name.
    """
    global quit_all
    name = inspect.stack()[0][3]
    try:
        if ch == 'q':
            logging.info("%s:%s Quitting." % (caller_name, name,))
            quit_all = True
    except Exception as e:
        handleException("%s:%s"%(caller_name,name), e)
        quit_all = True

def streamKeyboardStreams(config_sensor_streams):
    """Stream keyboard data.
    
    Args:
        config_sensor_streams: Keyboard streams,
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_kb_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_kb_streams: return
        while not quit_all and streamsNotDone(all_kb_streams):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    tstr = dateTimeToTimeString(t)
                    data = stream.getCurrentData()
                    if data:
                        handleCharacter(data, tstr, name, config)
                        if args.record: write_q.put((stream, t, data+"\n"))
                    stream.updateCurrent()
            time.sleep(0.001)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def writeData():
    """Removes data from the data queue and writes to appropriate stream.
    
    Calls get() on the data queue. Sleeps if the data is too new.
    When data is far enough in the past, writes to stream.
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    last_closed = currentTime(all_streams)
    try:
        logger = Logger(name, interval=60*5)
        while not (quit_all and write_q.empty()):
            logger.update()
            try:
                (stream, t, data) = write_q.get(timeout=writer_buffer_time)
                now = currentTime(all_streams)
                if (now-t).total_seconds() < writer_buffer_time:
                    time.sleep(writer_buffer_time)
            except:
                continue
            with writing_lock:
                stream.write(t, data)
                if (now-last_closed).total_seconds() > 1.0:
                    [v.close(t) for v in all_streams]
                    last_closed = now
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamAudioStreams(config_sensor_streams):
    """Stream audio data.
    
    Args:
        config_sensor_streams: Audio streams,
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_audio_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_audio_streams: return
        while not quit_all and streamsNotDone(all_audio_streams):
            logger.update()
            for streams in config_sensor_streams.values():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    data = stream.getCurrentData()
                    if args.record: write_q.put((stream, t, data))
                    stream.updateCurrent()
            time.sleep(0.001)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamCameraStreams(config_sensor_streams):
    """Stream camera data, setup visualization, and handle uncovering events.
    
    Stream camera data. Also display the vis image and handle user input.
    In the event of an uncovering (light=ON), create writers for
    appropriate setup.  For a covering (light=OFF), close the writers.
    Note that this function is run in the main thread.
    
    Args:
        config_sensor_streams: Camera streams.
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    ##writer = Cv2VideoWriter("demo.mp4", 25)
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True, memory_usage=True)
        all_camera_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_camera_streams: return
        # For each config, whether a camera is uncovered and how many frames recorded in this interval.
        uncovered, recorded = dict([(v, False) for v in config_sensor_streams.keys()]), {}
        vis_str, vis_shape = "vis", None
        vis_ims = dict([(v[0], [None for w in range(len(v[1]))]) for v in config_sensor_streams.items()])
        if args.display: cv2.namedWindow(vis_str)
        while (not quit_all and streamsNotDone(all_camera_streams)):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                if not streams: continue
                for (i, stream) in enumerate(streams):
                    # Read data and add to data queue.
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    #if uncovered[config]: print "Open", (t-t_open).total_seconds(), "secs"
                    tstr = dateTimeToTimeString(t)
                    im = stream.getCurrentData()
                    sm_im = resize(im, 1.0/args.display_downscale)
                    if vis_shape==None: vis_shape = sm_im.shape[:2]
                    if args.record:
                        write_q.put((stream,t,im))
                    stream.updateCurrent()
                    # Update the visualization for this stream.
                    c = (255,0,0) if config=="fridge" else (0,0,255)
                    #cv2.rectangle(sm_im, (0,0), (sm_im.shape[1]-1, sm_im.shape[0]-1), c, 10)
                    vis_ims[config][i] = sm_im
                light = 0 if None in vis_ims[config] else \
                        max([np.mean(np.max(v, axis=2)) for v in vis_ims[config]])
                # Handle state changes
                definitely_closed, definitely_open = light<50, light>100
                if not uncovered[config] and definitely_open:
                    t_open = t
                    logging.info("%s OPEN %s." % (name, tstr))
                    # Create writers.
                    if args.record:
                        with writing_lock:
                            [v.createWriter(t, time_buffer=writer_buffer_time, fps=30) \
                             for v in config_streams[config]]
                    # Send pulse command to expiring containers.
                    if args.msg_containers and api_config:
                        auth = ""
                        url_base = api_config["base-url"] + str(api_config["app-api-port"])
                        url = url_base + "/inventory"
                        irs = requests.get(url, headers={"Authorization":auth}).json()
                        alert_iids = [v["item_id"] for v in irs if v["remaining_time"] <= 0 \
                                      and "item_beacon_id" in v]
                        warning_iids = [v["item_id"] for v in irs \
                                        if v["remaining_time"] > 0 and v["remaining_time"] < 7 \
                                        and "item_beacon_id" in v]
                        data = {"item_ids": alert_iids, "animation": "ledOn",
                                      "duration": 3000, "color": "ff0000"}
                        url = url_base + "/containerAnimation?" + json.dumps(data)
                        requests.post(url, headers={"Authorization":auth})
                        data = {"item_ids": warning_iids, "animation": "ledOn",
                                      "duration": 3000, "color": "ff7700"}
                        url = url_base + "/containerAnimation?" + json.dumps(data)
                        requests.post(url, headers={"Authorization":auth})
                    uncovered[config], start_time, recorded[config] = True, time.time(), 0
                elif uncovered[config] and definitely_closed:
                    logging.info("%s CLOSED." % (name,))
                    fps = recorded[config] / (time.time()-start_time)
                    logging.info("%s video fps = %.1f." % (name, fps))
                    # Close writers.
                    if args.record:
                        with writing_lock:
                            [v.setWriterEndTimes(t) for v in config_streams[config]]
                    uncovered[config] = False
                if uncovered[config]: recorded[config] += 1
            vis_im = tileImages([cv2.resize(w, vis_shape[::-1]) if w!=None else np.zeros(vis_shape)\
                                 for v in vis_ims.values() for w in v])
            if args.display:
                cv2.imshow(vis_str, vis_im)
                handleCharacter(getKey(cv2.waitKey(1 if args.live else 10)), tstr, name, config)
            ##writer.write(vis_im)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamLoadCellStreams(config_sensor_streams):
    """Stream load cell data.
    
    Args:
        config_sensor_streams: Load cell streams,
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_load_cell_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_load_cell_streams: return
        while not quit_all and streamsNotDone(all_load_cell_streams):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    data = stream.getCurrentData()
                    if args.record: write_q.put((stream, t, "%f\n"%data))
                    stream.updateCurrent()
            time.sleep(0.005)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamRfidAntennaStreams(config_sensor_streams):
    """Stream RFID antenna data.
    
    Args:
        config_sensor_streams: RFID antenna streams.
    """
    global write_q, quit_all, config_tags
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_antenna_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_antenna_streams: return
        while not quit_all and streamsNotDone(all_antenna_streams):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    data = stream.getCurrentData()
                    if args.record:
                        [write_q.put((stream, v.time,str(v)+"\n")) for v in data]
                    # Update tags. List has unique tags with most recent
                    # reads and is in descending RSSI order.
                    tt = sorted(config_tags[config] + data, key=lambda x: x.time)
                    tt = dict([(v.epc, v) for v in tt if (t-v.time).total_seconds()<2]).values()
                    config_tags[config] = sorted(tt, key=lambda x: -x.rssi)
                    stream.updateCurrent()
            time.sleep(0.001)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamBarcodeStreams(config_sensor_streams):
    """Stream barcode data.
    
    Args:
        config_sensor_streams: barcode streams.
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_barcode_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_barcode_streams: return
        while not quit_all and streamsNotDone(all_barcode_streams):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    tstr = dateTimeToTimeString(t)
                    barcode = stream.getCurrentData()
                    if args.record:
                        if barcode: write_q.put((stream,barcode.time,str(barcode)+"\n"))
                    stream.updateCurrent()
            time.sleep(0.001)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def streamBleStreams(config_sensor_streams):
    """Stream BLE data.
    
    Args:
        config_sensor_streams: BLE streams.
    """
    global write_q, quit_all
    name = inspect.stack()[0][3]
    try:
        logger = Logger(name, interval=60*5, updates_per_second=True)
        all_ble_streams = [w for v in config_sensor_streams.values() for w in v]
        if not all_ble_streams: return
        while not quit_all and streamsNotDone(all_ble_streams):
            logger.update()
            for (config, streams) in config_sensor_streams.items():
                for stream in streams:
                    if passStream(stream, all_streams): continue
                    t = stream.getCurrentTime()
                    tstr = dateTimeToTimeString(t)
                    beacons = stream.getCurrentData()
                    if args.record:
                        for beacon in beacons:
                            write_q.put((stream,beacon.time,str(beacon)+"\n"))
                    stream.updateCurrent()
            time.sleep(0.001)
    except Exception as e:
        handleException(name, e)
        quit_all = True

def getKitchenInfo():
    db_config = json.loads(open(DB_CONFIG).read())
    name_to_kid = dict([(d["name"].lower(), d["id"]) for d \
                        in db_config["entries"]["Kitchen"]])
    hostname = socket.gethostname().lower()
    kid = name_to_kid[hostname]
    return kid, join(DATA, "Kitchen%07d" % kid)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Kitchen streaming.')
    parser.add_argument("--output", help="Output directory.")
    parser.add_argument("--fridge-config", help="Fridge configuration.")
    parser.add_argument("--api-config", help="Service configuration.")
    parser.add_argument("--frame-width", help="Frame width.", type=int)
    parser.add_argument("--frame-height", help="Frame height.", type=int)
    parser.add_argument("--display-downscale", help="Display downscale.", type=int, default=1)
    parser.add_argument("--live", help="Live stream.", action="store_true")
    parser.add_argument("--record", help="Record data.", action="store_true")
    parser.add_argument("--msg-containers", help="Msg containers.", action="store_true")
    parser.add_argument("--display", help="Display video.", action="store_true")
    args = parser.parse_args()
    
    if args.record and not args.live:
        print("Error: cannot record recorded stream.")
        parser.print_help()
        sys.exit(89)

    try:
        kitchen_id, output = getKitchenInfo()
    except Exception as e:
        print ("Error: must record from known machine.")
        sys.exit(89)
    
    if not args.output: args.output = output
            
    if args.frame_width and args.frame_height:
        shape = (args.frame_width, args.frame_height)
    elif not args.frame_width and not args.frame_height:
        shape = None
    else:
        print("Error: must specify both width and height or neither.")
        parser.print_help()
        sys.exit(89)

    configureLogging("%s.log" % args.output.rstrip("/"))
    
    api_config = None if not args.api_config else json.loads(open(args.api_config).read())
    configs = [FridgeConfig(args.fridge_config)]
        
    # TODO(jake): remove hack
    ble_addrs = ["f86aa431ba22"]

    # Initialize global list of config tags and all streams. The former is a dict
    # from config (eg, "fridge") to list of tags.
    # Latter is simply a list of streams.
    config_streams, config_tags = [dict([(w.name,[]) for w in configs]) \
                                   for v in range(2)]
    all_streams = []
    
    # Initialize control and stream threads.
    control_threads = [threading.Thread(target=v) for v in [writeData]]
    stream_threads = []    

    # For each stream type (eg, AudioStream, BarcodeStream), for each config, 
    # initialize and store the streams. Append to stream threads.
    stream_names = set([w for v in configs for w in v.recording_streams.keys()])
    for stream_name in stream_names:
        config_sensor_streams = {}
        for config in configs:
            sensor_names = config.recording_streams[stream_name]
            sensor_paths = [join(args.output, "%s%s%s"%(config.name,stream_name,v)) \
                            for v in sensor_names]
            for p in sensor_paths:
                if args.record and not exists(p): os.makedirs(p)
            if args.live: # Initialize StreamLive
                config_sensor_streams[config.name] = [eval(stream_name+"Live")(n, p, shape=shape, addrs=ble_addrs) \
                                                      for (n, p) in zip(sensor_names, sensor_paths)]
            else: # initialize StreamRecorded
                config_sensor_streams[config.name] = map(eval(stream_name+"Recorded"), sensor_paths)
            config_streams[config.name] += config_sensor_streams[config.name]
            all_streams += config_sensor_streams[config.name]
        if stream_name == "CameraStream":
            camera_config_streams = config_sensor_streams
        else:
            f = eval("stream%ss"%stream_name)
            stream_threads.append(threading.Thread(target=f, args=(config_sensor_streams,)))

    # Initialize global writer and control variables.
    write_q, writing_lock, writer_buffer_time = Queue.Queue(), threading.Lock(), 3.0
    quit_all = False

    # Kick off threads
    for t in control_threads+stream_threads:
        t.daemon = True
        t.start()
    
    # Stream camera data in main thread.
    streamCameraStreams(camera_config_streams)
    
    # Kick off and then join threads.
    [t.join() for t in stream_threads]
    quit_all = True
    [t.join() for t in control_threads]
    
    # Release all streams.
    [v.release() for v in all_streams]
