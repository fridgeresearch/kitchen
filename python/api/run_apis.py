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

Run apis.
"""

import sys, os, argparse, json, inspect, threading, requests, multiprocessing
from os.path import *
file_dir = dirname(abspath(__file__))
sys.path.append(dirname(dirname(abspath(__file__))))
from utils.logging_utils import *
from api.app_api import *
from api.ble_api import *
from api.ble_master import *

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--data", help="Data.", default=DATA)
    parser.add_argument("--log", help="Log file.")
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--init-handler", help="Initialize hash.", action='store_true')
    args = parser.parse_args()
    init_handler = args.init_handler
    
    if not args.log: args.log = default=join(args.data, "apis.log")
    configureLogging(args.log)
    config = json.loads(open(args.service_config).read())

    ble_url = config["base-url"] + str(config["ble-api-port"])    
    app_server = AppServerWrapper(config["host"], config["app-api-port"], config["db"],
                                  config["db-user"], config["db-passwd"], config["db-host"],
                                  ble_url, args.init_handler)
    ble_server = BleServerWrapper(config["ble-api-port"])
    master_server = BleMasterServerWrapper(config['ble-server'], config['ble-api-port'],
                                           config['ble-device-name'])
    
    ble_server.serveAsync()
    app_server.serveAsync()
    os.system("python %s/ble_master.py --data %s --service-config %s" % \
              (file_dir, args.data, args.service_config))
    #master_server.serveSync()
    ble_server.shutdown()
    app_server.shutdown()
    
