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
import argparse, os, sys, subprocess, pipes

CODE_DIR = "python/inventory/"

def pyScript(lines):
    return "\t@${IMPORT}\\\n\t"+";\\\n\t".join(lines)

def target(config, target):
    return "%s := \\\n\t%s\n"%(target, config[target])

def taskTargets(problem, names, task, ext):
    pdir = problem+"_DIR"
    key = "%s_%s_PATHS"%(problem.upper(), task.upper())
    config[key] = "\\\n\t".join([os.path.join("${%s}"%pdir, v+ext) for v in names])
    task_paths = target(config, key)
    p = problem.lower()
    task_deps = ""
    if task=="eval":
        if p!="inventory_estimation":
            task_deps = "fit_%s"%p
        else:
            task_deps = "eval_history_estimation fit_item_classification"
    elif task=="analyze":
        task_deps = "eval_%s"%p
    if problem.lower() == "history_estimation":
        task_deps = task_deps + " eval_cost_estimation "
    #clean_target = "clean_%s_%s: ${%s}\n"%(task.lower(), p, key)
    clean_target = "clean_%s_%s:\n%s\n"%(task.lower(), p, pyScript(["os.system('rm -f ${%s}')"%key]))
    task_target = "%s_%s: %s ${%s}\n"%(task.lower(), p, task_deps, key)
    path_target = "${%s}/%%%s:\n" % (pdir, ext)
    return "%s%s%s%s"%(task_paths, clean_target, task_target, path_target)

def taskPyScript(problem, models, task):
    key = "%s_%s_PATHS"%(problem.upper(), task.upper())
    py_lines = ["idx = '${%s}'.split().index('$@')"%key]
    if task.lower() != "analyze":
        py_lines.append("model, model_a, fit_a, eval_a, analyze_a = '${%s}'.split(';')[idx].split(',')"%models)
    return pyScript(py_lines)

def taskStr(problem, models, names, task, ext):
    return taskTargets(problem, names, task, ext) + taskPyScript(problem, models, task)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Parse Makefile configuration and output Makefile.')
    parser.add_argument("--input", help="Input Makefile configuration.", required=True)
    parser.add_argument("--output", help="Output Makefile.", required=True)
    args = parser.parse_args()
    
    # Parse configuration.
    t = "!@#$"
    config = map(lambda x: x.replace(t, "\\\n"), open(args.input).read().replace("\\\n", t).split('\n'))
    config = dict([map(lambda x: x.strip('\\\t\n '), v.strip().split(':=',1)) \
                   for v in config if len(v) and v.strip()[0]!="#"])
    # Write Makefile.
    output = open(args.output, "w")
    # Write common variables.
    output.write("SHELL := /usr/bin/python\n")
    output.write("IMPORT := import sys, os; from sys import stdout as std;"+\
                 "from os import listdir; from os.path import join;\n")
    output.write("OPENCV := ${HOME}/software/opencv-2.4.9/release/share/OpenCV\n\n")
    # Write code.
    output.write("all: code\n\n")
    output.write("code:\n"+pyScript(["os.system('%s')"%config["CODE"]])+"\n\n")
    # Write start and end variables.
    for k in ["START_FIT", "END_FIT", "START_EVAL", "END_EVAL"]:
        output.write("%s := %s\n"%(k, config[k]))
    # Create targets to fit, evaluate, and analyze
    # cost estimation, history estimation, and item classification problems.
    problems = ["COST_ESTIMATION", "HISTORY_ESTIMATION", "ITEM_CLASSIFICATION", "INVENTORY_ESTIMATION"]
    for problem in problems:
        p = problem.lower()
        # Target variables.
        output.write("\n# %s\n"%problem)
        output.write(target(config, problem+"_DIR"))
        models = problem.replace("ESTIMATION", "MODELS") if "ESTIMATION" in problem else \
                 problem.replace("CLASSIFICATION", "CLASSIFIERS")
        # Cost estimation, history estimation, and item classification.
        if problem != "INVENTORY_ESTIMATION":
            output.write(target(config, models))
            names = config[models+"_NAMES"].replace('\\', '').split()
            # Fit
            output.write(taskStr(problem, models, names, "fit", ".pkl")+";\\\n")
            s0 = "os.system('python %s/%s/fit.py "%(CODE_DIR,p) + "--o $@ --start ${START_FIT} %s "
            s1 = "--model %s --model-args %s --fit-args %s' % (model, model_a, fit_a))"
            not_ignore, ignore = s0%"--end ${END_FIT}" + s1, s0%"" + s1, 
            output.write("\t%s if 'ignoreend' not in '$*'.lower() else %s\n"%(not_ignore, ignore))
            # Eval
            output.write(taskStr(problem, models, names, "eval", "-eval.json")+";\\\n")
            output.write("\tp = '${%s_FIT_PATHS}'.split()[idx];\\\n"%problem)
            output.write("\tos.system('python %s/%s/eval.py "%(CODE_DIR,p)+\
                         "--o $@ --start ${START_EVAL} --end ${END_EVAL} "+\
                         "--i %s --eval-args %s' % (p, eval_a))\n")
        # Inventory Estimation
        else:
            # Eval
            classifier_names = config["ITEM_CLASSIFIERS_NAMES"].replace('\\', '').split()
            history_names = config["HISTORY_MODELS_NAMES"].replace('\\', '').split()
            names = ["%sHistory-%sClassifier"%(v,w) for v in history_names for w in classifier_names]
            output.write(taskTargets(problem, names, "eval", "-eval.json"))
            py_lines = [
                "history, classifier = os.path.splitext('$*')[0].split('-')",
                "history_fname = history.replace('History','')+'-eval.json'",
                "history_path = '${HISTORY_ESTIMATION_DIR}/'+history_fname",
                "classifier_fname = classifier.replace('Classifier','')+'.pkl'",
                "classifier_path = '${ITEM_CLASSIFICATION_DIR}/'+classifier_fname",
                "os.system('python %s/%s/%s.py "%(CODE_DIR, p, "eval")+\
                "--o $@ --start ${START_EVAL} --end ${END_EVAL} "+\
                "--history %s --classifier %s' % (history_path, classifier_path))"
            ]
            output.write(pyScript(py_lines)+"\n")            
        # Analyze
        output.write(taskStr(problem, models, names, "analyze", ".analysis")+";\\\n")
        output.write("\tp = '${%s_EVAL_PATHS}'.split()[idx];\\\n"%problem)
        output.write("\tos.system('python %s/%s/analyze.py "%(CODE_DIR, p)+\
                     "--o $@ --start ${START_EVAL} --end ${END_EVAL} "+\
                     "--i %s' % p)\n")
        tasks = ([] if p=="inventory_estimation" else ["fit"]) + ["eval", "analyze"]
        output.write("clean_%s: "%p+" ".join(["clean_%s_%s"%(v,p) for v in tasks])+"\n")
    
    # Clean
    output.write("\nclean_code:\n\trm -rf build/*\n")
    output.write("\nclean:\n")
    output.write(pyScript(["os.system('rm -f %s')" % ' '.join(['${%s_DIR}/*'%v for v in problems])])+"\n")
    
    output.close()
