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
import sys, os, MySQLdb as mdb, networkx as nx
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from utils.general_utils import *

# Function to return item arrival and removal event data.
def eventsArrivalsRemovals(events, items, item_str, arrival_prefix="", removal_prefix=""):
    arrivals = [[w[arrival_prefix+item_str] for w in items if w["arrivalevent_id"]==v["id"]] for v in events]
    removals = [[w[removal_prefix+item_str] for w in items if w["removalevent_id"]==v["id"]] for v in events]
    return arrivals, removals

# Function that returns data for item's arrival or removal event.
def getItemDataHelper(item, input_dir, item_event_id_str):
    if item[item_event_id_str]!=None:
        segm_dir = join(input_dir, "Events", "Segmentation%06d"%item[item_event_id_str])
        if exists(segm_dir):
            im_paths = [join(segm_dir, v) for v in os.listdir(segm_dir) \
                        if ".png" in v and int(splitext(v)[0].split('-')[-1])==item["item_id"]]
            ims = [cv2.imread(v) for v in im_paths]
            ft_paths = [join(segm_dir, v) for v in os.listdir(segm_dir) \
                        if "-cfc.npy" in v and int(v.split('-')[-2])==item["item_id"]]
            fts = [np.load(join(segm_dir, v)) for v in ft_paths]
            return im_paths, ims, ft_paths, fts
        else:
            return [], [], [], []
    else:
        return [], [], [], []

def getItemArrivalData(item, input_dir):
    return getItemDataHelper(item, input_dir, "arrivalevent_id")

def getItemRemovalData(item, input_dir):
    return getItemDataHelper(item, input_dir, "removalevent_id")

def getItemData(item, input_dir):
    ai_paths, ai, af_paths, af = getItemArrivalData(item, input_dir)
    ri_paths, ri, rf_paths, rf = getItemRemovalData(item, input_dir)
    return ai_paths+ri_paths, ai+ri, af_paths+rf_paths, af+rf

def getFoodDistances(graph, nodes=None, down_edge_cost=2.0):
    if nodes==None: nodes = graph.nodes()
    D = graph.copy()
    for (src, dst) in D.edges():
        D[src][dst]["weight"] = down_edge_cost
        D.add_edge(dst, src, weight=1.0)
    return dict([(v,nx.shortest_path_length(D, v, weight="weight")) for v in nodes])

def getFoodDistance(graph, fid_src, fid_dst, down_edge_cost=1.0):
    G = graph.to_undirected()
    path, cost, has_down = nx.shortest_path(G, fid_src, fid_dst), 0.0, False
    for (src, dst) in zip(path, path[1:]):
        if graph.has_edge(src, dst):
            cost += 1.0
        else:
            cost += down_edge_cost
    return cost
