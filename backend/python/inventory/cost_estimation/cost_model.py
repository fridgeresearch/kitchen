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
"""Arrival-Removal Basket Cost Model"""

# Authors: Jake T. Lussier <jake.t.lussier@gmail.com>

import sys, os, numpy as np
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from inventory.inventory_utils import *

INF = float("inf")

class CostModel(object):
    """Base abstract item Arrival-Removal Cost Model."""
    def fit(self):
        return

class CostModelGroundTruthItem(CostModel):
    """Arrival-Removal Cost Model that returns matrix reflecting ground truth item equality."""
    def eval(self, events, items, input_dir, constant=1e6):
        aids, rids = [map(set, v) for v in eventsArrivalsRemovals(events, items, "item_id")]
        assert(len(aids)==len(rids))
        return np.array([[INF if t_r<=t_a else (0.0 if a.intersection(r) else constant) \
                          for (t_r, r) in enumerate(rids)] for (t_a, a) in enumerate(aids)])

class CostModelGroundTruthFood(CostModel):
    """Arrival-Removal Cost Model that returns matrix reflecting ground truth food equality."""
    def eval(self, events, items, input_dir, constant=1e6):
        aids, rids = [map(set, v) for v in eventsArrivalsRemovals(events, items, "food_id")]
        return np.array([[INF if t_r<=t_a else (0.0 if a.intersection(r) else constant) \
                          for (t_r, r) in enumerate(rids)] for (t_a, a) in enumerate(aids)])

class CostModelUniform(CostModel):
    """Arrival-Removal Cost Model that returns a matrix of constants."""
    def eval(self, events, items, input_dir, constant=1e0):
        return np.array([[INF if t_r<=t_a else constant for t_r in range(len(events))] \
                         for t_a in range(len(events))])

class CostModelFc7(CostModel):
    """Arrival-Removal Cost Model that returns FC7 distance."""
    def eval(self, events, items, input_dir, missing_value=80.0):
        items = [v.copy() for v in items]
        for (i,item) in enumerate(items):
            items[i]["arrival_ftrs"] = getItemArrivalData(item, input_dir)[-1]
            items[i]["removal_ftrs"] = getItemRemovalData(item, input_dir)[-1]
        aftrs, rftrs = eventsArrivalsRemovals(events, items, "ftrs", "arrival_", "removal_")
        aftrs, rftrs = [[[ftrs for item_ftrs in event_ftrs for ftrs in item_ftrs] \
                         for event_ftrs in events_ftrs] for events_ftrs in [aftrs, rftrs]]
        return np.array([[INF if t_r<=t_a \
                          else(np.min([np.linalg.norm(af-rf) for af in a for rf in r])\
                               if r and a else missing_value) \
                          for (t_r, r) in enumerate(rftrs)] for (t_a, a) in enumerate(aftrs)])
        
