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
import argparse, sys, os, pickle, json
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from inventory.item_classification.item_classifier import *
from utils.general_utils import *
from db.db_utils import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--input", help="Input model pickle.", required=True)
    parser.add_argument("--output", help="Output eval file.", required=True)
    parser.add_argument("--data", help="Input data.", default=DATA)
    parser.add_argument("--eval-args", help="Eval args.", nargs='*', default=[])
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    args = parser.parse_args()
    
    assert(exists(args.input))
    assert(splitext(args.input)[1] == ".pkl")
    assert(splitext(args.output)[1] == ".json")
    
    # Load model.
    print "Evaluating model %s"%args.input
    model = pickle.load(open(args.input, "r"))
    
    # Load database.
    con, cursor = dbConnect()
    items = getItems(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id)
    graph = getFoodGraph(cursor)
    ancestors = getFoodAncestors(cursor, graph)
    
    # Eval.
    start_time = getEventTime(cursor, args.start_event_id)
    eval_args, eval_kwargs = parseArgs(args.eval_args)
    predicted_lbls, model_vis_paths = [], []
    food_names = getFoodNames(cursor)
    assert(not eval_args)
    for (i, item) in enumerate(items):
        #print "%d of %d" % (i+1, len(items))
        if item["arrivalevent_time"] < start_time: continue
        fid = model.classify(item, graph, ancestors, args.data, **eval_kwargs)
        item["food_id"], item["food_name"] = fid, food_names[fid]
        predicted_lbls.append(fid)
        model_vis_paths.append(model.vis_im_paths)
    # Save.
    json.dump([predicted_lbls, model_vis_paths], open(args.output, "w"))
