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
from utils.general_utils import *
from db.db_utils import *
from data_stream.fridge_stream import *
from config.fridge_config import *

def itemsToInventory(items, time=None):
    added = [v for v in items if v["arrivalevent_time"]==time]
    removed = [v for v in items if v["removalevent_time"]==time]
    inv = [v for v in items if not time or 
           (v["arrivalevent_time"]<=time and \
            (not v["removalevent_time"] or time<v["removalevent_time"]))]
    return inv, added, removed
    #return [v for v in items if not time or 
    #        (v["arrivalevent_time"]<=time and \
    #         (not v["removalevent_time"] or time<v["removalevent_time"]))]

def matchSets(ground_truth, predicted, dists, max_dist=0, max_weight=50):
    # construct graph
    G = nx.Graph()
    offset, n, wstr = 1e4, len(predicted), "iteminference_weight"
    G.add_nodes_from(enumerate(predicted), type="predicted")
    G.add_nodes_from(enumerate(ground_truth, n), type="groundtruth")
    edges = [(i, j, {"weight":int(offset-abs(p[wstr]-g[wstr]))}) \
             for (i,p) in enumerate(predicted) for (j,g) in enumerate(ground_truth,n) \
             if dists[p["food_id"]][g["food_id"]]<=max_dist]
    G.add_edges_from([e for e in edges if offset-e[2]["weight"]<max_weight])
    # match
    matches = [v for v in nx.max_weight_matching(G).items() if v[0]<len(predicted)]
    return zip(*[(predicted[u].copy(), ground_truth[v-len(predicted)].copy()) \
                 for (u, v) in matches])
    #return [v for v in nx.max_weight_matching(G).items() if v[0]<len(predicted)]
    #return [(predicted[v[0]], ground_truth[v[1]-len(predicted)]) \
    #        for v in nx.max_weight_matching(G).items() if v[0]<len(predicted)]
    """
    matches_p, matches_gt = zip(*[v for v in nx.max_weight_matching(G).items() if G.has_edge(*v)])
    #unmatched_gt = [v[1] for v in G.nodes(data=True) if v[0][-1]=="GroundTruth" and v[0] not in matches_gt]
    unmatched_p = [v[1] for v in G.nodes(data=True) if v[0][-1]=="Predicted" and v[0] not in matches_p]
    return matches, unmatched_gt, unmatched_p
    """

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--input", help="Input evaluation results.", required=True)
    parser.add_argument("--output", help="Output.", required=True)
    parser.add_argument("--data", help="Input data.", default=DATA)
    parser.add_argument("--config", help="Input configuration.", default=FRIDGE_FULL_CONFIG)
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    parser.add_argument("--visualize", help="Visualize")
    args = parser.parse_args()

    assert(os.path.splitext(args.input)[1] == ".json")
    assert(os.path.splitext(args.output)[1] == ".analysis")
    model_name = os.path.splitext(os.path.basename(args.input))[0].strip('-eval')

    # Load evaluation results.
    print "Analyzing results %s"%args.input
    fridge_items = json.loads(open(args.input).read())
    
    # Load database.
    con, cursor = dbConnect()
    D = getFoodGraph(cursor)
    fids = set([v["food_id"] for v in gt_items+items])
    dists = getFoodDistances(cursor, D, fids, down_edge_cost=1.0)
    max_dist = int(max([w for v in dists.values() for w in v.values()]))
    
    # Load stream and model.
    fridge_config = FridgeConfig(args.config)
    
    
    for fridge_id in [v["id"] for v in cursor.fetchall()]:
        fridge_dir = join(args.data, "Fridge%05d"%fridge_id)
        fridge_stream = FridgeStream(fridge_config, fridge_dir)
        items = fridge_items[fridge_id]
        gt_items = getItems(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                            fridge_id=fridge_id)
        events = getEvents(cursor, start_event_id=args.start_event_id, end_event_id=args.end_event_id, \
                           fridge_id=fridge_id)
"""
        # Analyze.
        mask_paths, gt_added_removed, p_added_removed = [], [], []
        accs_pd = [[] for w in range(max_dist+2)]
        for (i,t) in enumerate(change_times):
            #if i > 100: break
            print "%d of %d" % (i+1, len(change_times))
            gt_inv, gt_added, gt_removed = itemsToInventory(gt_items, t)
            p_inv, p_added, p_removed = itemsToInventory(items, t)
            cur_paths = [w for v in gt_added for w in getItemArrivalData(v, args.data)[0]]
            cur_paths += [w for v in gt_removed for w in getItemRemovalData(v, args.data)[0]]
            cur_paths = [v.replace(".png", ".json") for v in cur_paths]
            mask_paths.append(cur_paths)
            gt_added_removed.append((gt_added, gt_removed))
            p_added_removed.append((p_added, p_removed))
            for d in range(max_dist+1):
                p_matched, gt_matched = matchSets(gt_inv, p_inv, dists, max_dist=d, max_weight=50)
                p_unmatched = [v.copy() for v in p_inv if v not in p_matched]
                gt_unmatched = [v.copy() for v in gt_inv if v not in gt_matched]
                #intersection = 1.0*len(matches)
                #union = len(gt) + len(p) - intersection
                accs_pd[d+1].append(1.0*len(gt_matched)/len(gt_inv))
    
    
        
    
    
    # Plot and save.
    plt.figure()
    plt.plot(range(1, max_dist+2), [100*np.mean(v) for v in accs_pd[1:]])
    plt.title("%s\nFood Graph Distance vs. Accuracy"%model_name)
    plt.xlabel("Food Graph Distance")
    plt.ylabel("Accuracy")
    plt.ylim(-5, 105)
    if args.visualize: plt.show()
    plt.savefig(args.output.replace(".analysis", "-acc.png"))

    plt.figure()
    plt.title("%s\nAccuracy Over Time"%model_name)
    for d in range(1, max_dist+2):
        plt.plot([100.0*v for v in accs_pd[d]])
    plt.xlabel("Time (# of events)")
    plt.ylabel("Accuracy")
    #plt.legend(["Distance=%d"%v for v in range(1, max_dist+2)])
    lgd = plt.legend(["Distance=%d"%v for v in range(1, max_dist+2)],
                     loc="center left", bbox_to_anchor=(1, 0.5))
    plt.ylim(-5, 105)
    if args.visualize: plt.show()
    plt.savefig(args.output.replace(".analysis", "-acc-tseries.png"),
                bbox_extra_artists=(lgd,), bbox_inches='tight')
    
    # Visualization python script.
    json_fname = args.output.replace(".analysis", "-analysis.json")
    json.dump([mask_paths, gt_added_removed, p_added_removed, accs_pd], open(json_fname, "w"))
    f = open(args.output.replace(".analysis", "-analysis.py"), "w")
    f.write("import sys, cv2, json, numpy as np\n")
    f.write("sys.path.append('')\n")
    f.write("from db.db_utils import *\n")
    f.write("from utils.general_utils import *\n")
    f.write("from data_stream.fridge_stream import *\n")
    f.write("from config.fridge_config import *\n")
    f.write("mask_paths, gt_added_removed, p_added_removed, data = json.loads(open('%s').read())\n"%json_fname)
    f.write("# Load stream and model.\n")
    f.write("fridge_config = FridgeConfig('%s')\n"%args.config)
    f.write("fridge_stream = FridgeStream(fridge_config, '%s')\n"%args.data)
    f.write('''
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

d, n, n_prev, ims = 1, 0, -1, []
while True:
    print "graph dist=%d, accuracy=%.1f, event %d of %d"%(d, data[d][n] if len(data[d]) else 0.0, n+1, len(data[d]))
    if n != n_prev:
        ims = []
        for json_path in mask_paths[n]:
            camera_name, seg_name, d_idx, iid = os.path.splitext(os.path.basename(json_path))[0].split('-')
            s_idx = fridge_stream.getSegmentIndex(seg_name)
            im = fridge_stream.camera_streams[camera_name].getData(s_idx, int(d_idx))
            json_data = json.loads(open(json_path).read())
            color_hex = "#"+"".join([v+v for v in json_data[0]["stroke"][1:]])
            bgr = hex_to_rgb(color_hex)
            mask = json2image(json_data, *im.shape[:2])
            colored_mask = np.dstack([mask]*3) * bgr
            nonzero = np.nonzero(mask)
            im[nonzero] = np.clip(0.1*im+0.9*colored_mask, 0, 255).astype(np.uint8)[nonzero]
            if fridge_config.cameras[camera_name].orientation=="90":
                im = cv2.flip(cv2.transpose(im),0)
            ims.append(resize(im, 1.0/2))
        n_prev = n
    vis = tileImages(ims if ims else [np.zeros((256,256),dtype=np.uint)])
    words = (255*np.ones((vis.shape[0], 800, 3))).astype(np.uint8)
    y = 0
    y += 40
    cv2.putText(words, "Inventory Accuracy = %.2f"%data[d][n] if len(data[d]) else '?', \\
               (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0,0,0), thickness=4)
    y += 40
    for (s,(added, removed)) in [("Ground Truth", gt_added_removed[n]), ("Predicted", p_added_removed[n])]:
        y += 50
        cv2.putText(words, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0,0,0), thickness=4)
        y += 40        
        for (items, c) in [(added, '+'), (removed, '-')]:
            for item in items:
                cv2.putText(words, "%s%dg %s"%(c,int(item["iteminference_weight"]), item["food_name"]), \
                            (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,0), thickness=2)
                y += 40
    cv2.imshow("mask-ims", np.hstack((vis, words)))
    c = getKey(cv2.waitKey(0))
    if c=='J': d = (d-1) if d else (len(data)-1)
    elif c=='K': d = (d+1) if d<len(data)-1 else 0
    elif c=='j': n = (n-1) if n else (len(data[d])-1)
    elif c=='h': n = (n-10) if n-10 else (len(data[d])-1)
    elif c=='k': n = (n+1) if n < (len(data[d])-1) else 0
    elif c=='l': n = (n+10) if n+10 < (len(data[d])-1) else 0
    elif c=='q': break
    ''')
    
    open(args.output, "w").write("")
"""
