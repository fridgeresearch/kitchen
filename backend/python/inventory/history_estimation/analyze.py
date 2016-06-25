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
import sys, os, argparse, json
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from utils.general_utils import *
from db.db_utils import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--input", help="Input evaluation results.", required=True)
    parser.add_argument("--output", help="Output.", required=True)
    parser.add_argument("--data", help="Input directory.", default=DATA)
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    args = parser.parse_args()

    assert(exists(args.input))
    assert(splitext(args.input)[1] == ".json")
    assert(splitext(args.output)[1] == ".analysis")
    model_name = splitext(basename(args.input))[0].strip('-eval')
    
    # Load evaluation results.
    print "Analyzing results %s"%args.input
    fridge_items = json.loads(open(args.input).read())

    # Load database.
    con, cursor = dbConnect()
    
    # Visualization python script.
    json_fname = args.output.replace(".analysis", "-analysis.json")
    #json.dump([obj], open(json_fname, "w"))
    f = open(args.output.replace(".analysis", "-analysis.py"), "w")
    f.write("import sys, cv2, json, numpy as np\n")
    f.write("sys.path.append('')\n")
    f.write("from db.db_utils import *\n")
    f.write("from utils.general_utils import *\n")
    #f.write("obj = json.loads(open('%s').read())[0]\n"%json_fname)
    f.write('''
print "No analysis!"
''')
    f.close()
    
    open(args.output, "w").write("\n")
    
