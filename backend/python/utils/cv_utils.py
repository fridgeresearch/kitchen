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
import sys, os, math, numpy as np, cv2
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

class Cv2Plotter:
    def __init__(self, miny=0.0, maxy=1.0, memory=100.0, canvas_size=(480, 640), line_width=2):
        self.miny, self.rangey, self.memory = miny, maxy-miny, memory
        self.colors = []
        (self.height, self.width), self.line_width = canvas_size, line_width
    def plot(self, data, im=None):
        if im==None: im = np.ones((self.height, self.width, 3), dtype=np.uint8)*255
        for i in range(len(self.colors), len(data)):
            self.colors.append(np.random.randint(0,255,3))
        for (line_data, color) in zip(data, self.colors):
            line_pts = [(int(1.0*x/self.memory*self.width+self.width),
                         int(self.height-1.0*(y-self.miny)/self.rangey*self.height))\
                        for (x,y) in line_data]
            [cv2.line(im, u, v, color, self.line_width) for (u, v) in zip(line_pts, line_pts[1:])]
        return im

class StreamingPlotter:
    def __init__(self, miny=0.0, maxy=1.0, memory=10.0):
        self.lines, self.to_ind = [], {}
        self.plotter = Cv2Plotter(miny=miny, maxy=maxy, memory=memory)
    def update(self, t, key, val):
        if key not in self.to_ind:
            self.to_ind[key] = len(self.to_ind.keys())
            self.lines.append([])
        self.lines[self.to_ind[key]].append((t, val))
    def plot(self, time):
        lines = [[((x-time).total_seconds(),y) for (x,y) in v] for v in self.lines]
        return self.plotter.plot(lines)

def getKey(c):
    c = c if c < 256 else c & 0xFF
    if c not in range(256): return ''
    return chr(c)

class Cv2VideoWriter:
    def __init__(self, filename, fps):
        self.basename, self.ext = splitext(filename)
        if self.ext not in [".avi", ".mp4"]:
            raise Exception("Unknown video type: %s." % ext)
        self.fc, self.fps = cv2.VideoWriter_fourcc(*'XVID'), fps
        self.writer, self.shape = None, None
    def write(self, im):
        res = tuple(im.shape[:2][::-1])
        if self.writer == None:
            self.res = res
            self.writer = cv2.VideoWriter(self.basename+".avi", self.fc, self.fps, self.res)
        if res != self.res:
            raise Exception("Inappropriate image shape: %s." % str(im.shape))
        self.writer.write(im)
    def close(self):
        if not self.writer: return # TODO(jake): how handle this?
        self.writer.release()
        del self.writer
        if self.ext == ".mp4":
            log = "/tmp/%s.log" % basename(self.basename)
            if exists("%s.mp4"%self.basename):
                os.remove("%s.mp4"%self.basename)
            if os.system("avconv -i %s.avi -r %d %s.mp4 2>%s" % (self.basename,self.fps,self.basename,log)):
                raise Exception("Could not convert %s.avi. See logfile at %s." % (self.basename, log))
            os.system("rm %s.avi" % self.basename)

def convertToBgr(im):
    if im.dtype != np.uint8: im = np.clip((im*255), 0, 255).astype(np.uint8)
    if len(im.shape) < 3: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    return im

def tileImages(ims, shape=None, row_major=True):
    if not shape:
        shape = tuple([int(math.sqrt(math.ceil(math.sqrt(len(ims)))**2))]*2)
    elif shape[0]==None:
        shape = (len(ims)/shape[1] + len(ims)%shape[1], shape[1])
    elif shape[1]==None:
        shape = (shape[0], len(ims)/shape[0] + len(ims)%shape[0])
    shape = list(shape)
    i, j = (0, 1) if row_major else (1, 0)
    shape[i] = int(math.ceil(1.0*len(ims)/shape[j]))
    h, w = ims[0].shape[:2]
    for (i, im) in enumerate(ims):
        assert(im.shape[:2] == (h, w))
        ims[i] = convertToBgr(im)
    tiled = np.zeros((h*shape[0], w*shape[1], 3), np.uint8)
    for (i, im) in enumerate(ims):
        loc = (i/shape[1], i%shape[1]) if row_major else (i%shape[0], i/shape[0])
        loc = (h*loc[0], w*loc[1])
        tiled[loc[0]:loc[0]+h, loc[1]:loc[1]+w, :] = im
    return tiled

def resize(im, scale_factor):
    s = im.shape
    return cv2.resize(im, (int(s[1]*scale_factor), int(s[0]*scale_factor)))
