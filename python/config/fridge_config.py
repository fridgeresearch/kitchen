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
import sys, os, json, numpy as np, cv2
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.general_utils import *
from utils.math_utils import *
from kitchen import *

class FridgeElement:
    def __init__(self, section, x, y, z, roll, pitch, yaw, T_parent_in_world=np.eye(4)):
        self.section = section
        self.x, self.y, self.z = x, y, z
        self.roll, self.pitch, self.yaw = roll, pitch, yaw
        self.T_self_in_parent, self.T_self_in_world = None, None
        if None not in [x,y,z,roll,pitch,yaw]:
            self.T_self_in_parent = getTransformFromTranslationEuler(x, y, z, roll, pitch,yaw)
            self.T_self_in_world = T_parent_in_world.dot(self.T_self_in_parent)
        self.points_in_self = np.zeros((4,1))
        self.points_in_self[3] = 1.0

class FridgeBoxElement(FridgeElement):
    def __init__(self, section, x, y, z, roll, pitch, yaw, w, h, d, T_parent_in_world=np.eye(4)):
        FridgeElement.__init__(self, section, x, y, z, roll, pitch, yaw, T_parent_in_world)
        self.w, self.h, self.d = w, h, d
        self.points_in_self = np.zeros((4,1))
        self.points_in_self[3] = 1.0
        for (x, z) in [(0.0, self.d), (self.w, self.d), (self.w, 0.0)]:
            self.points_in_self = np.hstack((self.points_in_self, np.array([[x], [self.h], [z], [1.0]])))

class FridgeScaleElement(FridgeBoxElement):
    def __init__(self, section, surface, x, y, z, roll, pitch, yaw, w, h, d, T_parent_in_world=np.eye(4)):
        FridgeBoxElement.__init__(self, section, x, y, z, roll, pitch, yaw, w, h, d, T_parent_in_world)
        self.surface = surface
    
    def planePointInWorld(self, x, y):
        x, y = map(millimetersToMeters, [x, y])
        #object_in_self = np.array([self.w/2+x, 0.0, self.d/2-y, 1.0])
        object_in_self = np.array([self.w/2+x, 0.0, inchesToMeters(1.0)+y, 1.0])
        object_in_world = self.T_self_in_world.dot(object_in_self)
        return object_in_world[:3]
    """
    def planePointInWorld(self, y, x):
        object_in_self = np.array([self.w/2+x, 0.0, self.d/2-y, 1.0])
        object_in_world = self.T_self_in_world.dot(object_in_self)
        return object_in_world[:3]
    """

class FridgeMarkerElement(FridgeBoxElement):
    def __init__(self, section, x, y, z, roll, pitch, yaw, size, T_parent_in_world=np.eye(4)):
        FridgeElement.__init__(self, section, x, y, z, roll, pitch, yaw, T_parent_in_world)
        self.size = size
        self.points_in_self = np.array([[0,0,0,1], [size,0,0,1], [size,size,0,1], [0,size,0,1]]).T

class FridgeConfig:
    def __init__(self, config_fname):
        config = convertToStrings(json.loads(open(config_fname).read())) if config_fname else {}
        #print config_fname
        #print config
        scales_config_path = config["scales-config"] if "scales-config" in config else SCALES_CONFIG
        self.scales_config = convertToStrings(json.loads(open(scales_config_path).read()))
        self.sections, self.surfaces = {}, {}
        self.antennas, self.cameras, self.load_cells, self.markers, self.scales = {}, {}, {}, {}, {}
        self.name = "fridge"
        fridge = config[self.name] if self.name in config else {}
        self.keyboards = fridge["keyboards"] if "keyboards" in fridge else {}
        self.antennas = fridge["antennas"] if "antennas" in fridge else {}
        self.bles = fridge["bles"] if "bles" in fridge else {}
        #print self.keyboards
        #print "keyboards" in fridge
        #sys.exit(89)
        sections = fridge["sections"] if "sections" in fridge else {}
        for (section_name, section) in sections.items():
            self.sections[section_name] = FridgeBoxElement(section, *self._getPoseVars(section))
            self.sections[section_name].surfaces = {}
            for (surface_name, surface) in section["surfaces"].items() if "surfaces" in section else []:
                el = FridgeBoxElement(section, *self._getPoseVars(surface))
                #assert(abs(el.x - (self.sections[section_name].w-el.w)/2) <= 1e-6)
                self.surfaces[surface_name] = el
                self.surfaces[surface_name].scales = {}
                T = self.surfaces[surface_name].T_self_in_world
                for (scale_name, scale) in surface["scales"].items() if "scales" in surface else []:
                    el = FridgeScaleElement(section, surface, *self._getPoseVars(scale), T_parent_in_world=T)
                    key = "template-name"
                    if key in scale: el.template = scale[key]
                    #assert(el.w == self.surfaces[surface_name].w)
                    #assert(el.d == self.surfaces[surface_name].d)
                    self.scales[scale_name] = el
                    self.surfaces[surface_name].scales[scale_name] = el
                    for i in range(3):
                        load_cell_name = "%s-%d"%(scale_name,i)
                        self.load_cells[load_cell_name] = {} # TODO ?
                self.sections[section_name].surfaces[surface_name]=self.surfaces[surface_name]
            if "markers" in section:
                self.sections[section_name].markers = {}
                for (marker_name, marker) in section["markers"].items():
                    self.markers[marker_name] = FridgeMarkerElement(section, *self._getPoseVars(marker))
                    self.sections[section_name].markers[marker_name] = self.markers[marker_name]
            self.sections[section_name].cameras = {}
            for (camera_name, camera) in section["cameras"].items() if "cameras" in section else []:
                cam_el = FridgeElement(section, *self._getPoseVars(camera))
                cam_el.orientation = camera["orientation"]
                cam_el.visible_surfaces = camera["visible-surfaces"]
                self.cameras[camera_name] = cam_el
                self.sections[section_name].cameras[camera_name] = cam_el
            """
            self.sections[section_name].antennas = {} # TODO?
            for (antenna_name, antenna) in section["antennas"].items() if "antennas" in section else []:
                self.antennas[antenna_name] = {}
                self.sections[section_name].antennas[antenna_name] = {}
            """
        self.recording_streams = dict([("AudioStream", []),
                                       ("BarcodeStream", []),
                                       ("BleStream", self.bles.keys()),
                                       ("CameraStream", self.cameras.keys()),
                                       ("KeyboardStream", self.keyboards.keys()),
                                       ("LoadCellStream", self.load_cells.keys()),
                                       ("RfidAntennaStream", self.antennas.keys())])

    def _getPoseVars(self, d):
        if "template-name" in d: # scale width / depth / height from template
            d["height"] = 0.0
            verts = self.scales_config[d["template-name"]]["components"]["top"]
            x, y = zip(*verts)
            # TODO: specify units in scales config
            d["width"], d["depth"] = [(max(v)-min(v))*0.0254 for v in [x,y]]
        fields = ["x","y","z","roll","pitch","yaw",
                  "width","height","depth", "rows","cols","cell-size", "size"]
        vals = []
        for val in [d[v] for v in fields if v in d]:
            if val=='?':
                vals.append(None)
            elif type(val) in [int, float]:
                vals.append(val)
            else:
                vals.append(parseMeasure(val))
        return vals

def drawWorld(im, fridge_config, camera_name, T_world_in_camera):
    camera = fridge_config.cameras[camera_name]
    section = [v for v in fridge_config.sections.values() if camera in v.cameras.values()][0]
    vis_im = 1*im
    if T_world_in_camera==None: return vis_im
    scale_pts = [(scale.T_self_in_world.dot(scale.points_in_self),'r')\
                 for (surface_name, surface) in section.surfaces.items() \
                 for surface in section.surfaces.values() \
                 for scale in surface.scales.values()]
    marker_pts = [(marker.T_self_in_world.dot(marker.points_in_self),'b') \
                  for (m, marker) in section.markers.items()]
    for (pts_in_world, color) in scale_pts+marker_pts:
        color = [255,0,0] if color=='b' else [0,0,255]
        im_pts = []
        pts_in_camera = T_world_in_camera.dot(pts_in_world)
        for (i,pt_in_camera) in enumerate(list(pts_in_camera.T)):
            u, v = map(int, projectPoint(pt_in_camera, CAMERA_CMAT))
            if u<0 or u>=im.shape[1] or v<0 or v>=im.shape[0]:
                im_pts.append((u, v, False))
            else:
                im_pts.append((u, v, True))
                cv2.circle(vis_im, (u, v), 5, thickness=1 if i else 3, color=color)
        im_pts.append(im_pts[0])
        [cv2.line(vis_im, im_pts[i][:2], im_pts[i+1][:2], color, 10) \
         for i in range(len(im_pts)-1) if im_pts[i][-1] or im_pts[i+1][-1]]
    return vis_im
