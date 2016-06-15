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

Program that visualizes a fridge model in 3D.
"""
import argparse, sys, os, math, numpy as np, matplotlib.pyplot as plt, json, scipy as sp
import matplotlib.colors as colors
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from itertools import product, combinations
from kitchen_model import *

class Arrow3D(FancyArrowPatch):
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0,0), (0,0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))
        FancyArrowPatch.draw(self, renderer)

def orderedIndices(corners):
    added = [corners[0]]
    for it in range(3):
        added.append(sorted([(np.linalg.norm(added[-1][1]-v[1]), v) for v in corners if v not in added])[0][1])
    return [v[0] for v in added]

def drawBox(T, w, h, d, top_face_color=None, back_face_color=None):
    scaling = np.array([w,h,d,1])
    r = [0,1]
    unit_corners = np.array([v+(1,) for v in product(r,r,r)])
    line_pairs = [(i,j) for (i,j) in combinations(range(8),2) \
                      if np.sum(np.abs(unit_corners[i]-unit_corners[j]))==1]
    corners = [T.dot(scaling*v)[:3] for v in unit_corners]
    [ax.plot3D(*zip(corners[i], corners[j]), color='b') for (i,j) in line_pairs]
    for (quad_idx, quad_color) in [(1, top_face_color), (2, back_face_color)]:
        if quad_color==None: continue
        quad = orderedIndices([(i,c) for (i,c) in enumerate(unit_corners) if c[quad_idx]==1])
        collection = Poly3DCollection([[corners[i] for i in quad]], alpha=0.1)
        collection.set_facecolor(quad_color)
        ax.add_collection3d(collection)
        #ax.scatter(*zip(*[corners[i][:3] for i in quad]), color=quad_color, s=10)

def drawMarker(T, size, color):
    corners = np.array([((0, 0, 0, 1), (size, 0, 0, 1)), \
                        ((size, 0, 0, 1), (size, size, 0, 1)), \
                        ((size, size, 0, 1), (0, size, 0, 1)), \
                        ((0, size, 0, 1), (0, 0, 0, 1))])
    #corners = np.array([((0, size, 0, 1), (size, size, 0, 1)), \
    #                    ((size, size, 0, 1), (size, 0, 0, 1)), \
    #                    ((size, 0, 0, 1), (0, 0, 0, 1)), \
    #                    ((0, 0, 0, 1), (0, size, 0, 1))])
    corners = [T.dot(v.T)[:3].T for v in corners]
    [ax.plot3D(*zip(u, v), color=color) for (u, v) in corners]
    r = corners[0][0]
    ax.scatter(r[0], r[1], r[2], color='r', s=50)

def drawChessboard(T, rows, cols, cell_size):
    idx = 0
    for r in range(-1,rows):
        for c in range(-1,cols):
            poly = []
            for (dr, dc) in [(0,0),(0,cell_size),(cell_size,cell_size),(cell_size,0)]:
                poly.append(np.array([c*cell_size+dc, r*cell_size+dr, 0.0, 1.0]))
            poly = [list(T.dot(v)[:3]) for v in poly]
            collection = Poly3DCollection([poly], alpha=0.5)
            collection.set_color('k' if (not r%2 and not c%2) or (r%2 and c%2) else 'w')
            ax.add_collection3d(collection)
            if not r and not c:
                ax.scatter([poly[0][0]], [poly[0][1]], [poly[0][2]], color='r', s=50)
            idx += 1
    return T

def drawAxis(T, length=0.2):
    for (i,c) in zip(range(3), ["b","g","r"]):
        origin = [0.0]*3 + [1.0]
        dest = [0.0 if v!=i else length for v in range(3)] + [1.0]
        origin, dest = [T.dot(v)[:3] for v in [origin, dest]]
        ax.add_artist(Arrow3D(*zip(origin,dest), mutation_scale=20, lw=5, arrowstyle="-|>", color=c))

if __name__ == "__main__":
 
    parser = argparse.ArgumentParser(description='Visualize fridge blueprint.')
    parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG)
    args = parser.parse_args()
    
    fridge_config = FridgeConfig(args.config)
    
    fig = plt.figure()
    for (i, section_name) in enumerate(["main", "door"]):
        section = fridge_config.sections[section_name]
        # Setup plotting section
        ax = fig.add_subplot(1,len(fridge_config.sections), i+1, projection='3d')
        plt.title(section_name)
        ax.set_aspect("equal")

        [ax.set_xlabel(v) for v in ["x", "y", "z"]]

        unit_len = max([abs(v) for v in [section.w, section.d, section.h]])+0.2
        ax.set_xlim(section.w/2-unit_len/2, section.w/2+unit_len/2)
        ax.set_ylim(section.h/2-unit_len/2, section.h/2+unit_len/2)
        ax.set_zlim(section.d/2-unit_len/2, section.d/2+unit_len/2)
        ax.view_init(-90, -90)
        
        # Draw axis for the coordinate system
        drawAxis(np.eye(4))
        # Draw the fridge
        drawBox(section.T_self_in_world, section.w, section.h, section.d, back_face_color='b')
        # Draw each surface.
        for surface in section.surfaces.values():
            drawBox(surface.T_self_in_world, surface.w, surface.h, surface.d)
            # Draw the surface's scales.
            for scale in surface.scales.values():
                drawBox(scale.T_self_in_world, scale.w, scale.h, scale.d, top_face_color='r')
        # Draw each marker.
        for marker in section.markers.values():
            if marker.T_self_in_world != None:
                drawMarker(marker.T_self_in_world, marker.size, 'b')
                #drawBox(marker.T_self_in_world, marker.w, marker.h, marker.d, top_face_color='r')
                #marker_T = drawMarker(marker.T_self_in_world, marker.rows, marker.cols, marker.cell_size)
    plt.show()
