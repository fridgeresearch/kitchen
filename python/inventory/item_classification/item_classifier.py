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
"""Item Classification"""

# Authors: Jake T. Lussier <jake.t.lussier@gmail.com>

import sys, os
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from utils.general_utils import *

class ItemClassifier(object):
    """Base abstract item classifier."""
    def fit(self, items, input_dir):
        self.vis_im_paths = []
        return
    def classify(self, item, food_graph, food_ancestors, input_dir, map_leaf=True, min_score=None, **kwargs):
        kwargs = convertKwargs(kwargs)
        scores = self.eval(item, food_graph, food_ancestors, input_dir, **kwargs)
        score, fid = max([(0 if min_score==None else len(food_ancestors[fid]), score, fid) \
                          for (fid, score) in scores.items() \
                          if (min_score==None or score >= min_score) and \
                          (not map_leaf or not food_graph[fid])])[1:]
        return fid
    def _propagateDown(self, graph, fid, scores):
        children, score = graph[fid], scores[fid]
        for child in children:
            scores[child] += 1.0*score/len(children)
            self._propagateDown(graph, child, scores)
        return
        
class ItemClassifierGroundTruth(ItemClassifier):
    """Item Classifier that returns ground truth."""
    def __init__(self, **kwargs):
        super(ItemClassifierGroundTruth, self).__init__(**kwargs)
    def eval(self, item, food_graph, food_ancestors, input_dir):
        scores = dict([(v, 0.0) for v in food_ancestors.keys()])
        for f in food_ancestors[item["food_id"]]: scores[f] = 1.0
        self._propagateDown(food_graph, item["food_id"], scores)
        return scores
