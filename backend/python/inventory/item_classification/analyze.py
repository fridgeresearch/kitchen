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
import argparse, sys, os, sqlite3, json, numpy as np, matplotlib.pyplot as plt
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from inventory.inventory_utils import *
from utils.general_utils import *
from db.db_utils import *

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
    predicted_lbls, model_vis_paths = json.loads(open(args.input).read())
    
    # Load database.
    con, cursor = dbConnect()

    # Get items.
    items = getItems(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id)
    start_time = getEventTime(cursor, args.start_event_id)
    items = [v for v in items if v["arrivalevent_time"] >= start_time]
    paths = [getItemData(v, args.data)[0] for v in items]
    assert(len(items)==len(predicted_lbls))
    
    # Construct food graph distance dictionary.
    D = getFoodGraph(cursor)
    D_known = D.copy()
    cursor.execute("SELECT id FROM Food WHERE name='Unbranded'")
    deleteSubtree(D_known, cursor.fetchone()["id"])
    cursor.execute("SELECT id FROM Food WHERE name='Branded Unknown'")
    deleteSubtree(D_known, cursor.fetchone()["id"])
    fids = set([v["food_id"] for v in items] + predicted_lbls)
    dists = getFoodDistances(D, fids, down_edge_cost=1.0)
    max_dist = int(max([w for v in dists.values() for w in v.values()]))
    
    # Evaluate.
    food_names = getFoodNames(cursor)
    data, corrects_pd, corrects_bpd = [[[] for w in range(max_dist+2)] for v in range(3)]
    for (item, predicted_lbl, mp, p) in zip(items, predicted_lbls, model_vis_paths, paths):
        dist = int(dists[predicted_lbl][item["food_id"]])
        #data[dist].append((p, mp, food_names[predicted_lbl], item["food_name"]))
        for d in range(max_dist+1): corrects_pd[d+1].append(dist<=d)
        if item["food_id"] in D_known:
            data[dist].append((p, mp, food_names[predicted_lbl], item["food_name"]))
            for d in range(max_dist+1): corrects_bpd[d+1].append(dist<=d)
    
    # Plot and save.
    for (cpd, s) in [(corrects_pd, "All"), (corrects_bpd, "Branded")]:
        plt.figure()
        plt.plot(range(1, max_dist+2), [100*np.mean(v) for v in cpd[1:]], '-o')
        plt.title("%s %s Food Graph Distance vs. Accuracy"%(model_name, s))
        plt.xlabel("Food Graph Distance")
        plt.ylabel("Accuracy")
        plt.ylim(-5, 105)
        if args.visualize: plt.show()
        #plt.savefig(args.output.replace(".analysis", "-graph_dist_vs_correct.png"))
        plt.savefig(args.output.replace(".analysis", "-%s_graph_dist_vs_correct.png"%s.lower()))
    
    # Visualization python script.
    json_fname = args.output.replace(".analysis", "-analysis.json")
    json.dump(data, open(json_fname, "w"))
    f = open(args.output.replace(".analysis", "-analysis.py"), "w")
    f.write("import sys, cv2, json, numpy as np\n")
    f.write("sys.path.append('')\n")
    f.write("from db.db_utils import *\n")
    f.write("from utils.general_utils import *\n")
    f.write("data = json.loads(open('%s').read())\n"%json_fname)
    f.write('''
d, n = 0, 0
while True:
    if data[d]:
        paths, model_paths, predicted, gt = data[d][n]
        print "graph dist=%d, predicted=%s, ground-truth=%s"%(d, predicted, gt)
        ims, mims = [map(cv2.imread, v) if v else [np.zeros((256,256), dtype=np.uint8)] \\\n
                     for v in [paths, model_paths]]
        cv2.imshow("instance", tileImages(ims))
        cv2.imshow("model-vis", tileImages(mims))
    else:
        print "No predicted at distance %d from ground truth."%d
    c = getKey(cv2.waitKey(0))
    if c=='J': d, n = d-1 if d else len(data)-1, 0
    elif c=='K': d, n = d+1 if d<len(data)-1 else 0, 0
    elif c=='j': n = n-1 if n else len(data[d])-1
    elif c=='k': n = n+1 if n < len(data[d])-1 else 0
    elif c=='q': break
''')
    f.close()

    open(args.output, "w").write("")
