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
"""Item Weight and Removal (aka History) Model"""

# Authors: Jake T. Lussier <jake.t.lussier@gmail.com>

import sys, os
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from utils.general_utils import *
from inventory.history_estimation.optimization import *

class HistoryModel(object):
    """Base abstract model."""
    def fit(self):
        return

class HistoryModelOptimization(HistoryModel):
    def eval(self, events, gt_items, C, **kwargs):
        kwargs = convertKwargs(kwargs)
        obj, baskets = optimizeBasketWeights(events, C, **kwargs)
        items = basketsToItems(baskets, events)
        return obj, items

class HistoryModelGroundTruth(HistoryModel):
    def eval(self, events, gt_items, C, **kwargs):
        return 0.0, gt_items
