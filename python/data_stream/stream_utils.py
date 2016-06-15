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
import argparse, sys, os, datetime, time, inspect, logging, select, threading, cv2, Queue
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from data_stream.audio_stream_live import *
from data_stream.audio_stream_recorded import *
from data_stream.barcode_stream_live import *
from data_stream.barcode_stream_recorded import *
from data_stream.ble_stream_live import *
from data_stream.ble_stream_recorded import *
from data_stream.camera_stream_live import *
from data_stream.camera_stream_recorded import *
from data_stream.component_stream_live import *
from data_stream.component_stream_recorded import *
from data_stream.keyboard_stream_live import *
from data_stream.keyboard_stream_recorded import *
from data_stream.load_cell_stream_live import *
from data_stream.load_cell_stream_recorded import *
from data_stream.rfid_antenna_stream_live import *
from data_stream.rfid_antenna_stream_recorded import *
from data_stream.scale_stream_live import *
from data_stream.scale_stream_recorded import *

streamsNotDone = lambda x: [v for v in x if not v.done]

def currentTime(streams):
    times = [v.getCurrentTime() for v in streamsNotDone(streams)]
    if not times:
        return None
    else:
        return min(times)

def passStream(stream, streams):
    t = currentTime(streams)
    return stream.done or (stream.getCurrentTime()-t).total_seconds() > 0.1

def checkStreamArgs(parser, data, sensors):
    # 00 --> nonsense
    if not sensors and not data:
        print("Error: must provide either data or sensors.")
    # 11 --> live record
    #elif sensors and data and [v for v in data if exists(v)]:
    #    print("Error: output directory exists.")
    # 01 --> recorded read
    elif not sensors and data and [v for v in data if not exists(v)]:
        print("Error: input directory does not exist.")
    # 10 --> live no record all good
    # Else all good.
    else:
        if data and sensors:
            [os.makedirs(v) for v in data if not exists(v)]
        return
    sys.exit(89)
