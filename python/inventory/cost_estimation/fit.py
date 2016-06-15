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
import sys, os, argparse, pickle
from os.path import *
sys.path.append(dirname(dirname(dirname(abspath(__file__)))))
from kitchen import *
from cost_model import *
from utils.general_utils import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument("--model", help="Model name.", required=True)
    parser.add_argument("--output", help="Output model pickle.", required=True)
    parser.add_argument("--model-args", help="Model args.", nargs='*', default=[])
    parser.add_argument("--fit-args", help="Fit args.", nargs='*', default=[])
    parser.add_argument("--start-event-id", help="Start event id.", type=int)
    parser.add_argument("--end-event-id", help="End event id.", type=int)
    args = parser.parse_args()
    
    assert(splitext(args.output)[1] == ".pkl")
    assert(args.model.replace("CostModel", "")+".pkl"==basename(args.output))
    
    print "Fitting model %s"%args.output
    model_args, model_kwargs = parseArgs(args.model_args)
    model = eval(args.model)(*model_args, **model_kwargs)
    
    # Fit
    fit_args, fit_kwargs = parseArgs(args.fit_args)
    model.fit(*fit_args, **fit_kwargs)
    
    # Write model.
    pickle.dump(model, open(args.output, "w"))
