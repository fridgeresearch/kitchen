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

Module that provides load cell functionality.
"""
import threading, time, Queue, matplotlib.pyplot as plt
import Phidgets.PhidgetException, Phidgets.Devices.Bridge, Phidgets.Manager

class LoadCell():
    """Class storing a load cell (bridge and bridge input).
    
    Class storing a load cell (bridge and bridge input). List of all bridge
    inputs is shared amongst all load cells.
    
    
    Attributes:
        all_bridge_inputs: List of all bridge inputs (class variable).
        loader_lock: Lock ensures atomic bridge input loading (class variable).
        bridge: Phidget bridge.
        bridge_input: Bridge input.
    """    
    all_bridge_inputs, loader_lock = None, threading.Lock()
    def __init__(self, bridge, bridge_input):
        if LoadCell.all_bridge_inputs == None:
            with LoadCell.loader_lock:
                LoadCell.all_bridge_inputs = getBridgeInputs()
        self.bridge, self.bridge_input = [v for v in self.all_bridge_inputs if \
                                          bridge==v[0].getSerialNum() and bridge_input==v[1]][0]
        self.prev_data = None

    def read(self, timeout=0.1):
        timeout_time = time.time() + timeout
        data = self._getData()
        while self.prev_data==data and time.time() < timeout_time:
            data = self._getData()
        self.prev_data = 1*data
        return data

    def _getData(self):
        return self.bridge.getBridgeValue(self.bridge_input)
            

def _initBridge(sn):
    bridge = Phidgets.Devices.Bridge.Bridge()
    bridge.openPhidget(serial=sn)
    bridge.waitForAttach(5000)
    bridge.setDataRate(8)
    return bridge

# Input:  List of load cell names (eg., "343532-0")
# Output: List of corresponding (bridge_input, index) pairs.
def getBridgeInputs(names=None):
    bridge_dict = {}
    if names == None:
        mngr = Phidgets.Manager.Manager()
        mngr.openManager()
        time.sleep(2.0)
        names = []
        for device in mngr.getAttachedDevices():
            sn = device.getSerialNum()
            bridge_dict[sn] = _initBridge(sn)
            names += ["%s-%d"%(sn, i) for i in range(3)]
    bridge_inputs = []
    for name in names:
        sn, i = map(int, name.split('-'))
        if sn not in bridge_dict:
            bridge_dict[sn] = _initBridge(sn)
        bridge = bridge_dict[sn]
        bridge.setEnabled(i, True)
        bridge.setGain(i, Phidgets.Devices.Bridge.BridgeGain.PHIDGET_BRIDGE_GAIN_8)
        bridge_inputs.append((bridge, i))
    while True:
        try:
            [b.getBridgeValue(i) for (b, i) in bridge_inputs]
            break
        except Exception as e:
            pass
    return bridge_inputs

class LoadCellVisualizer():
    def __init__(self, n, miny=-0.2, maxy=0.4, q_size=100, win_size=11):
        if not n: return
        self.win_size = win_size
        self.colors = None
        self.qs = [Queue.Queue(maxsize=q_size) for v in range(n)]
        fig=plt.figure()
        self.ax = fig.add_subplot(111)
        plt.title("Load Cell Readings")
        plt.xlabel("Timesteps Back")
        plt.ylabel("Reading")
        plt.axis([-q_size+1,0,miny,maxy])
        plt.ion()
        plt.show()

    def update(self, idx, data):
        if self.qs[idx].full(): self.qs[idx].get()
        self.qs[idx].put(data)
        #x = [symmetricWindowedAverage(list(v.queue), self.win_size) for v in self.qs]
        x = [list(v.queue) for v in self.qs]
        if not self.colors:
            data = [w for v in x for w in [range(-len(v)+1, 1), v]]
        else:
            data = [w for (c, v) in zip(self.colors, x) for w in \
                    [range(-len(v)+1,1), v, c]]
        lines = self.ax.plot(*data)
        self.colors = self.colors if self.colors else [v.get_color() for v in lines]
        plt.draw()
        [lines.pop(0).remove() for v in range(len(lines))]

    def getData(self):
        return [list(v.queue) for v in self.qs]
