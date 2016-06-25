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
import math, numpy as np

INCHES_TO_METERS = 0.0254

DEGREES_TO_RADIANS = math.pi/180

def inchesToMeters(x):
    return x * INCHES_TO_METERS

def metersToInches(x):
    return x / INCHES_TO_METERS

def metersToMillimeters(x):
    return x*1e3

def millimetersToMeters(x):
    return x*1e-3

def inchesToMillimeters(x):
    return metersToMillimeters(inchesToMeters(x))

def millimetersToInches(x):
    return metersToInches(millimetersToMeters(x))

def degreesToRadians(x):
    return x * DEGREES_TO_RADIANS

def radiansToDegrees(x):
    return x / DEGREES_TO_RADIANS

# Procedures for rotation conversions from http://euclideanspace.com/maths/geometry/rotations/conversions/index.htm

# roll (aka bank, psi) is rotation about x
# pitch (aka attitude, phi) is rotation about z
# yaw (aka heading, theta) is rotation about y
def eulerToMatrix(roll, pitch, yaw):
    ch, sh = math.cos(yaw), math.sin(yaw)
    ca, sa = math.cos(pitch), math.sin(pitch)
    cb, sb = math.cos(roll), math.sin(roll)
    R = np.eye(3)
    R[0,0] = ch * ca
    R[0,1] = sh*sb - ch*sa*cb;
    R[0,2] = ch*sa*sb + sh*cb;
    R[1,0] = sa;
    R[1,1] = ca*cb;
    R[1,2] = -ca*sb;
    R[2,0] = -sh*ca;
    R[2,1] = sh*sa*cb + ch*sb;
    R[2,2] = -sh*sa*sb + ch*cb;
    return R

def matrixToEuler(R):
    roll = math.atan2(-R[1,2], R[1,1])
    pitch = math.asin(R[1,0])
    yaw = math.atan2(-R[2,0], R[0,0])
    return roll, pitch, yaw

def getTransformFromTranslationEuler(x, y, z, roll, pitch, yaw):
    T = np.eye(4)
    T[:3, :3] = eulerToMatrix(roll,pitch,yaw)
    T[:3, 3] = [x,y,z]
    return T

def getTranslationEulerFromTransform(T):
    x, y, z = T[:3, 3]
    roll, pitch, yaw = matrixToEuler(T[:3, :3])
    return x, y, z, roll, pitch, yaw

def getTransformFromRt(R, t):
    return np.vstack((np.hstack((R, t)), np.array([0,0,0,1.0])))

def getInverseTransform(T):
    R, t = T[:3, :3], T[:3,3]
    return getInverseTransformFromRt(R, t)

def getInverseTransformFromRt(R, t):
    return np.vstack((np.hstack((R.T, -R.T.dot(t).reshape((3,1)))), np.array([0,0,0,1.0])))

def projectPoint(pt, cmat):
    u = cmat[0][0]*pt[0]/pt[2] + cmat[0][2]
    v = cmat[1][1]*pt[1]/pt[2] + cmat[1][2]
    return (u, v)
