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
import sys, os
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from data_stream.stream_live import *
from audio.audio_reader import *
from audio.audio_writer import *

class AudioStreamWriter(StreamWriter):
    """Class for writing audio stream data.
    """
    def __init__(self, out_path, start_time, time_buffer, **kwargs):
        StreamWriter.__init__(self, out_path, start_time, time_buffer)
    def _createDataFile(self):
        self.data_file = AudioWriter(join(self.out_path,"sound.wav"))

class AudioStreamLive(StreamLive):
    """Class for streaming live audio data.
    
    Class for streaming live audio data. Wrapper around an AudioReader.
    
    Attributes:
        reader: AudioReader.
    """
    # TODO(jake): remove name (there so can provide in stream_kitchen.py)
    def __init__(self, name=None, out_path=None, **kwargs):
        """Initialize live audio stream."""
        StreamLive.__init__(self, out_path, **kwargs)
        self.writer_class = AudioStreamWriter
        self.reader = AudioReader(**kwargs)
        
    def getCurrentData(self):
        """Get the current data.
        
        Get the current data returned from the reader's read() method.
        """
        return self.reader.read()

    def release(self):
        """Release the audio reader."""
        StreamLive.release(self)
        return self.reader.release()
