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
import argparse, sys, os, sqlite3, pickle, json
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from inventory.item_classification.item_classifier import *
from inventory.inventory_utils import *
from utils.general_utils import *
from db.db_utils import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--history", help="Input history.", required=True)
    parser.add_argument("--classifier", help="Input classifier.", required=True)
    parser.add_argument("--output", help="Output eval file.", required=True)
    parser.add_argument("--data", help="Input data.", default=DATA)
    parser.add_argument("--classify-args", help="Classify args.", nargs='*', default=[])
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    args = parser.parse_args()
    
    assert(splitext(args.history)[1] == ".json")
    assert(splitext(args.classifier)[1] == ".pkl")
    
    # Load model.
    print "Evaluating inventory estimation %s"%basename(args.output)
    classifier = pickle.load(open(args.classifier, "r"))
    
    # Load database.
    con, cursor = dbConnect()
    graph = getFoodGraph(cursor)
    ancestors = getFoodAncestors(cursor, graph)
    food_names = getFoodNames(cursor)
    food_id = [k for (k, v) in food_names.items() if v=="Food"][0]
    
    # Load history.
    fridge_items = json.loads(open(args.history).read())

    # Get "ground truth" food labels in case need ground truth for classification.
    classify_args, classify_kwargs = parseArgs(args.classify_args)
    for fridge_id in [v["id"] for v in cursor.fetchall()]:
        fridge_dir = join(args.data, "Fridge%05d"%fridge_id)
        items = fridge_items[fridge_id]
        gt_items = getItems(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                            fridge_id=fridge_id)
        events = getEvents(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                           fridge_id=fridge_id)
        arrival_fids, removal_fids = eventsArrivalsRemovals(events, gt_items, "food_id")
        for (i, item) in enumerate(items):
            event_inds = [j for (j,v) in enumerate(events) if v["id"]==item["arrivalevent_id"] or \
                          v["id"]==item["removalevent_id"]]
            fids = arrival_fids[event_inds[0]] + (removal_fids[event_inds[1]] if len(event_inds)>1 else [])
            items[i]["food_id"] = fids[0] if fids else food_id
        # Eval.
        for (i, item) in enumerate(items):
            print "%d of %d" % (i+1, len(items))
            fid = classifier.classify(item, graph, ancestors, fridge_dir, **classify_kwargs)
            item["food_id"], item["food_name"] = fid, food_names[item["food_id"]]
    
    # Save.
    json.dump(fridge_items, open(args.output, "w"))
