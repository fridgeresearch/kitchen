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

Program to update Kitchen database.
"""
import sys, os, argparse, json
from os.path import *
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kitchen import *
from db.db_handler import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Update database.')
    parser.add_argument("--db-config", help="Db configuration.", default=DB_CONFIG)
    parser.add_argument("--create", help="Create database.", action="store_true")
    parser.add_argument("--drop", help="Drop existing database.", action="store_true")
    parser.add_argument("--insert", help="Insert from config into database.", action="store_true")
    parser.add_argument("--service-config", help="Service config.", default=PROCESSING_CONFIG)
    args = parser.parse_args()

    config = json.loads(open(args.service_config).read())
    handler = DatabaseHandler(config["db"], config["db-user"], config["db-passwd"],
                              config["db-host"], create=args.create)
    json_data = json.loads(open(args.db_config).read())
    if args.drop:
        handler.dropDatabase()
        handler.createDatabase()
    for (table, cols) in json_data["tables"].items():
        cols, col_props = zip(*[v.split(' ',1) for v in cols])
        table_cols = [("%s.%s"%(table, v)).lower() for v in cols]
        if handler.tableExists(table): # update
            entries = handler.get([table])
            entries = [dict([(k,v) for (k,v) in entry.items() if k.lower() in table_cols])\
                       for entry in entries]
            handler.dropTable(table)
            handler.createTable(table, cols, col_props)
            handler.insertMany(table, entries)
        else: # create
            handler.createTable(table, cols, col_props)
    handler.commit()
    if args.insert:
        for (table, objs) in json_data["entries"].items():
            for obj in objs:
                c = ["%s.id=%d"%(table, obj["id"])]
                if "id" not in obj or not handler.get([table], constraints=c):
                    handler.insert(table, obj)
                else:
                    handler.update(table, obj, constraints=c)
        #[handler.insertMany(table, objs) for (table, objs) in json_data["entries"].items()]
    handler.commit()
