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
import sys, os, pyaudio, array
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

class AudioReader():
    """Class for reading audio data.
    
    Reads data using PyAudio.
    """

    def __init__(self):
        """Initialize AudioReader.
        
        Creates and opens PyAudio stream."""
        r = pyaudio.PyAudio()
        self.stream = r.open(format=pyaudio.paInt16, channels=1, rate=44100, 
                             input=True, output=True, frames_per_buffer=AUDIO_CHUNK)
        
    def read(self):
        """Read audio data."""
        return array.array('h', self.stream.read(AUDIO_CHUNK))

    def release(self):
        """Release audio resources."""
        self.stream.stop_stream()
        self.stream.close()
