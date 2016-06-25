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
import sys, os, argparse, json, urllib2, requests
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from db.db_handler import *

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--food", help="Food name.", nargs='+')
    parser.add_argument("--animation", help="Animation name.", required=True)
    parser.add_argument("--color", help="Color.", default="ffffff")
    parser.add_argument("--duration", help="Duration.", type=float, default=3000)
    args = parser.parse_args()
    
    #if not args.food and not args.all:
    #    print("Must provide --food <arg> or --all.")
    #    sys.exit(0)
    
    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"],
                              config["db-passwd"], config["db-host"])
    if args.food:
        c = ["Item.food_id=Food.id", "Food.name='%s'"%(' '.join(args.food))]
    else:
        c = []
    iids = [v["Item.id"] for v in handler.get(["Item", "Food"], constraints=c)]
    ble_url = config["base-url"] + str(config["app-api-port"]) + "/containerAnimation?"
    data = {"animation": args.animation, "item_ids": iids}
    if args.animation != "ledOff":
        if args.color: data["color"] = args.color
        if args.duration: data["duration"] = args.duration
    url = ble_url+json.dumps(data)
    print "url =", url
    auth = ""
    requests.post(url, headers={"Authorization":auth})
