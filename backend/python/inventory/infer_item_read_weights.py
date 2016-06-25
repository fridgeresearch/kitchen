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

Program to infer weights and weight bounds for ItemRead entries.
"""
import argparse, sys, os, json
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from inventory.history_estimation.optimization import *
from db.db_utils import *
from db.db_handler import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    parser.add_argument("--service-config", help="Service config.", default=PROCESSING_CONFIG)
    args = parser.parse_args()
    
    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"], config["db-host"])
    
    # Process each kitchen.
    for row in handler.get(["Kitchen"]):
        kitchen_id = row["Kitchen.id"]
        events = handler.getEvents(kitchen_id=kitchen_id)
        item_reads = handler.getItemReads(kitchen_id=kitchen_id)
        item_reads = clearWeightData(item_reads)
        obj, item_reads = optimizeItemReadWeights(events, item_reads)
        item_reads = optimizeItemReadWeightBounds(events, item_reads)
        # Update item weights in db.
        for ir in item_reads:
            obj = dict([(v, ir["ItemRead.%s"%v]) \
                        for v in ["min_weight", "max_weight", "weight"]])
            obj["weight_known"] = int(obj["max_weight"] != None and obj["min_weight"] != None and \
                                      (obj["max_weight"]-obj["min_weight"]) < MAX_STABLE_FORCE)
            handler.update("ItemRead", obj, ["id=%d"%ir["ItemRead.id"]])
    handler.commit()
    
