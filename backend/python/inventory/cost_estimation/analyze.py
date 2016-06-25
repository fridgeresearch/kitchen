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
import argparse, sys, os, sqlite3, numpy as np, json, matplotlib.pyplot as plt
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from utils.general_utils import *
from db.db_utils import *
from cost_model import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--input", help="Input evaluation results.", required=True)
    parser.add_argument("--output", help="Output.", required=True)
    parser.add_argument("--data", help="Input directory.", default=DATA)
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    parser.add_argument("--visualize", help="Visualize")
    args = parser.parse_args()

    assert(exists(args.input))
    assert(splitext(args.input)[1] == ".json")
    assert(splitext(args.output)[1] == ".analysis")
    model_name = splitext(basename(args.input))[0].strip('-eval')

    # Load evaluation results.
    print "Analyzing results %s"%args.input
    Cs = dict([(int(k),np.array(v)) for (k,v) in json.loads(open(args.input).read()).items()])
    print Cs.keys()

    # Load database.
    con, cursor = dbConnect()

    out_file = open(args.output.replace(".analysis", "-stats.txt"), "w")
    cursor.execute("SELECT id FROM Fridge")
    data = {}
    for fridge_id in [v["id"] for v in cursor.fetchall()]:
        fridge_dir = join(args.data, "Fridge%05d"%fridge_id)
        # Get events, items, and arrival / removal data.
        items = getItems(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                         fridge_id=fridge_id)
        events = getEvents(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                           fridge_id=fridge_id)
        C = Cs[fridge_id]
        assert((len(events), len(events))==C.shape)
        for (i, item) in enumerate(items):
            items[i]["arrival_paths"] = getItemArrivalData(item, fridge_dir)[0]
            items[i]["removal_paths"] = getItemRemovalData(item, fridge_dir)[0]
        apaths, rpaths = eventsArrivalsRemovals(events, items, "paths", "arrival_", "removal_")
        apaths, rpaths = [[[paths for item_paths in event_paths for paths in item_paths] \
                           for event_paths in events_paths] for events_paths in [apaths, rpaths]]
        aids, rids = eventsArrivalsRemovals(events, items, "item_id")
        # Evaluate
        data[fridge_id], is_correct, correct_min_cost, all_min_cost = [], [], [], []
        for (t_a, event) in enumerate(events):
            candidates = sorted([(C[t_a][t_r], rpaths[t_r], rids[t_r]) for (t_r, e) in enumerate(events)])
            corrects = [v for v in candidates if len(set(aids[t_a]).intersection(set(v[-1])))]
            if not corrects: continue
            data[fridge_id].append([(apaths[t_a], aids[t_a])+v for v in candidates])
            is_correct.append(corrects[0]==candidates[0])
            correct_min_cost.append(corrects[0][0])
            all_min_cost.append(candidates[0][0])
    
        if is_correct:
            stats = 1.0*sum(is_correct)/len(is_correct), np.mean(correct_min_cost), np.mean(all_min_cost)
        else:
            stats = 1.0, 1.0, 1.0
        out_file.write("%.2f %.2f %.2f\n"%stats)
    out_file.close()

    # Visualization python script.
    json_fname = args.output.replace(".analysis", "-analysis.json")
    json.dump(data, open(json_fname, "w"))
    f = open(args.output.replace(".analysis", "-analysis.py"), "w")
    f.write("import sys, cv2, json, numpy as np\n")
    f.write("sys.path.append('')\n")
    f.write("from utils.general_utils import *\n")
    f.write("from utils.cv_utils import *\n")
    f.write("data = json.loads(open('%s').read())\n"%json_fname)
    f.write('''
d, n, fridge_idx = 0, 0, 0
while True:
    fridge_id = sorted(data.keys())[fridge_idx]
    arrival_paths, arrival_iids, cost, removal_paths, removal_iids = data[fridge_id][d][n]
    correct = len(set(arrival_iids).intersection(set(removal_iids))) > 0
    print "arrival=%d, rank=%d, cost=%.2f, correct=%s" % (d, n, cost, correct)
    aims, rims = [map(cv2.imread, v) if v else [np.zeros((256,256), dtype=np.uint8)] \\
                  for v in [arrival_paths, removal_paths]]
    cv2.imshow("arrival", tileImages(aims))
    cv2.imshow("removal", tileImages(rims))
    c = cv2.waitKey(0)
    c = c if c < 256 else c & 0xFF
    c = chr(c) if c in range(256) else ''
    if c=='J': d, n = d-1 if d else len(data)-1, 0
    elif c=='K': d, n = d+1 if d<len(data)-1 else 0, 0
    elif c=='j': n = n-1 if n else len(data[d])-1
    elif c=='k': n = n+1 if n < len(data[d])-1 else 0
    elif c=='f': fridge_idx = max(0, fridge_idx-1)
    elif c=='F': fridge_idx = min(0, fridge_idx+1)
    elif c=='q': break
''')
    f.close()
