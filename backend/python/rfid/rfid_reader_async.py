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
"""
import sys, os, subprocess, datetime, threading, Queue
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from rfid.rfid_tag_read import *

RFID_RUN = ("java -cp %s/software/mercuryapi-1.27.2.34/java/demo.jar:" + 
            "%s/software/mercuryapi-1.27.2.34/java/ltkthingmagic.jar:" + \
                "%s/software/mercuryapi-1.27.2.34/java/ltkjava-1.0.0.6.jar:" + \
                "%s/software/mercuryapi-1.27.2.34/java/mercuryapi.jar:bin") % tuple([expanduser("~")]*4)

class RfidReaderAsync():
    """Class for reading RFID tags.
    
    Class for reading RFID tags. Runs the Mercury Java program.
    
    Attributes:
       proc: Process that runs recording program asynchronously.
       max_time: max_time to store tag before discarding.
       power: Reader power.
       antenna_tags: Dictionary from antenna to tag list.
       listen_thread: Thread that listens to the Java program.
    """
    #def __init__(self, delay=100, max_time=1.0, interface="eth", power=3000, session="S0"):
    def __init__(self, interface, max_time=1.0, power=None, session=None):
        cmd = "cd %s && %s rfid.RfidReaderAsync %s %s %s" % \
              (KITCHEN_DIR, RFID_RUN, interface, ("readPower=%d"%power) if power else "",
               ("session=%s"%session) if session else "")
        self.proc = subprocess.Popen(cmd, shell=True, 
                                     stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        self.max_time, self.power = max_time, power
        self.antenna_tags = {}
        self.listen_thread = threading.Thread(target=self._listen)
        self.listen_thread.daemon = True; self.listen_thread.start()

    def getPower(self):
        return self.power

    def setPower(self, power):
        self.power = power
        self.proc.stdin.write('readPower=%d\n'%power)
           
    def setSession(self, session):
        self.proc.stdin.write('session=%d\n'%session)
 
    def release(self):
        self.proc.stdin.write('q\n')
        self.listen_thread.join()
    
    def _listen(self):
        while True:
            line = self.proc.stdout.readline().strip()
            if not line: break
            tag = RfidTagRead(*line.split())
            a = tag.antenna
            if a not in self.antenna_tags: self.antenna_tags[a] = Queue.Queue()
            self.antenna_tags[a].put(tag)
            t = datetime.datetime.utcnow()
            tag.time, tag.time_str = t, dateTimeToTimeString(t) # TODO(jake): remove if good stamps
            for a in self.antenna_tags.keys():
                while not self.antenna_tags[a].empty():
                    t = datetime.datetime.utcnow()
                    try:
                        td = (t-self.antenna_tags[a].queue[0].time).total_seconds()
                        if td > self.max_time:
                            self.antenna_tags[a].get()
                        else: break
                    except Exception as e:
                        # Queue might have been emptied between checking empty and accessing.
                        pass

    def read(self, antennas=None):
        if antennas==None: antennas = self.antenna_tags.keys()
        tags = []
        for a in [v for v in antennas if v in self.antenna_tags]:
            while not self.antenna_tags[a].empty():
                tags.append(self.antenna_tags[a].get_nowait())
        return tags
