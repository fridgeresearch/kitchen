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

Program to stream live or recorded BLE data and print codes.
"""
import sys, os, argparse, select
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.ble_stream_live import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Detect new BLE devices.')
    args = parser.parse_args()
    
    s = BleStreamLive()
    addrs = set([])
    while True:
        beacons = s.getCurrentData()
        for beacon in beacons:
            if beacon.addr not in addrs:
                print "NEW BEACON:", beacon.addr
                addrs.add(beacon.addr)
        r = select.select([sys.stdin], [], [], 0.1)[0]
        if r and sys.stdin.readline()[:-1]=='q': break
    s.release()
