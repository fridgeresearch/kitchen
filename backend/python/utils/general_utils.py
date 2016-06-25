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
import sys, os, datetime, collections, psutil, dateutil.parser, smtplib, numpy as np
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from utils.math_utils import *

def sendEmail(from_addr, to_addrs, subject, msg):
   server = smtplib.SMTP('smtp.gmail.com', '587')
   server.starttls()
   psswd = ""
   server.login(from_addr, psswd)
   msg = 'Subject: %s\n\n%s' % (subject, msg)
   server.sendmail(from_addr, to_addrs, msg)
   server.quit() 

def timeStringToDateTime(time_string):
    return dateutil.parser.parse(time_string)

def dateTimeToTimeString(date_time):
    TIME_FORMAT = "%Y%m%dT%H%M%S.%f"
    return date_time.strftime(TIME_FORMAT)

def datetimeToUnix(t):
    return (t-datetime.datetime(1970,1,1)).total_seconds()

def parseMeasure(s):
    val, unit = s.strip().split()
    val = float(val)
    if unit == "m" or unit == "rad":
        return val
    elif unit == "in":
        return inchesToMeters(val)
    elif unit == "deg":
        return degreesToRadians(val)
    else:
        raise Exception("Unrecognized unit: %s." % unit)

def convertToStrings(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convertToStrings, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convertToStrings, data))
    else:
        return data

def convertKwarg(val):
    try:
        return float(val) if "." in val else int(val)
    except Exception as e:
        if val in ["True", "False"]: return eval(val)
        else: return val

def convertKwargs(kwargs):
    converted = {}
    for (key, val) in kwargs.items():
        converted[key] = convertKwarg(val)
    return converted

def parseArgs(args):
    reg_args, kwargs = [], {}
    for arg in args:
        if "=" in arg:
            key, val = arg.split("=", 1)
            kwargs[key] = val
        else:
            reg_args.append(arg)
    return reg_args, kwargs

# Offset functions.
def symmetricOffsets(n, win_size):
    return [(min(n-1-v, v, win_size/2),)*2 for v in range(n)]

def leftRightOffsets(n, win_size):
    return [(min(v,win_size/2), min(n-1-v,win_size/2)) for v in range(n)]

def leftRightDeltaOffsets(n, values, delta):
    l = [max([i-j for j in range(i+1) if values[i]-values[j]<delta]) \
         for i in range(n)]
    r = [max([j-i for j in range(i,n) if values[j]-values[i]<delta]) \
         for i in range(n)]
    return zip(l, r)

# Application functions.
def maxDiff(array):
    return max(array) - min(array)

# General windowed function.
def windowedFunction(apply_fun, offset_fun, array, args=None):
    n = len(array)
    return [apply_fun(array[i-a:i+b+1]) for (i,(a,b)) \
            in zip(range(n), offset_fun(n, *args) if args else offset_fun(n))]

# Specific instances.
def symmetricWindowedAverage(array, win_size=5):
    return windowedFunction(np.mean, symmetricOffsets, array,args=(win_size,))

def leftRightWindowedAverage(array, win_size=5):
    return windowedFunction(np.mean, leftRightOffsets, array,args=(win_size,))

def symmetricWindowedMaxDiff(array, win_size=5):
    return windowedFunction(maxDiff, symmetricOffsets, array,args=(win_size,))

def leftRightWindowedMaxDiff(array, win_size=5):
    return windowedFunction(maxDiff, leftRightOffsets, array,args=(win_size,))

def symmetricWindowedMax(array, win_size=5):
    return windowedFunction(max, symmetricOffsets, array, args=(win_size,))

def leftRightWindowedMax(array, win_size=5):
    return windowedFunction(max, leftRightOffsets, array, args=(win_size,))

def timeWindowedAverage(array, times, delta):
    return windowedFunction(np.mean, leftRightDeltaOffsets,\
                            array, args=(times,delta))

def timeWindowedMaxDiff(array, times, delta):
    return windowedFunction(maxDiff, leftRightDeltaOffsets,\
                            array, args=(times,delta))

def timeWindowedMax(array, times, delta):
    return windowedFunction(max, leftRightDeltaOffsets,\
                            array, args=(times,delta))
