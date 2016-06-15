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
import sys, os, logging, datetime#, psutil

def configureLogging(filename=None):
    fs = unicode('%(asctime)s %(levelname)s:%(message)s',)
    ds = unicode('%b  %-d %H:%M:%S')
    logging.basicConfig(filename=filename, format=fs, datefmt=ds, level=logging.DEBUG)
    if filename:
        console = logging.StreamHandler()
        formatter = logging.Formatter(fs, datefmt=ds)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

def handleException(name, e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    logging.error("%s Error @ line %d: %s ." % (name, exc_tb.tb_lineno, e))

class Logger:
    def __init__(self, name, interval=60, updates_per_second=False, memory_usage=False):
        logging.debug("%s initializing logger"%(name,))
        self.name = name
        self.start = datetime.datetime.utcnow()
        self.interval_len = interval
        self.interval_ups = 0
        self.interval_start = self.start
        self.updates_per_second = updates_per_second
        #self.proc = psutil.Process(os.getpid()) if memory_usage else None
    def __del__(self):
        logging.debug("%s deleting Logger." % (self.name,))
    def update(self):
        self.interval_ups += 1
        t  = datetime.datetime.utcnow()
        dt = (t-self.interval_start).total_seconds()
        if dt > self.interval_len:
            logging.debug("%s %d seconds" % (self.name, (t-self.start).total_seconds()))
            if self.updates_per_second:
                per_sec = 1.0*self.interval_ups/self.interval_len
                logging.debug("%s %.1f updates per sec" % (self.name, per_sec))
            # TODO(jake): cross-platform way to do memory_percent()
            #if self.proc != None:
            #    logging.debug("%s %.1f%% memory usage" % (self.name, self.proc.memory_percent()))
            self.interval_start, self.interval_ups = t, 0
