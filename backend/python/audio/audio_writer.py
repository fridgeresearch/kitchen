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
import sys, os, pyaudio, wave, array, struct
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

class AudioWriter:
    """Class for buffering and saving audio data.
    
    Buffers audio data with write() calls and saves data upon release().
    """
    def __init__(self, path):
        """Initialize AudioWriter with the output path
        
        Args:
            path: Audio file output path.
        """
        self.path = path
        self.data = []

    def write(self, data):
        """Write (actually buffer) audio data.
        
        Args:
            data: audio data vector to add to our buffer.
        """
        self.data.extend(data)
        
    def close(self):
        """Save the buffered data and release resources."""
        p = pyaudio.PyAudio()
        sample_width, audio_rate = p.get_sample_size(pyaudio.paInt16), 44100
        r = self.data
        audio_array = struct.pack('<' + ('h'*len(r)), *r)
        wf = wave.open(self.path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(audio_rate)
        wf.writeframes(audio_array)
        wf.close()
