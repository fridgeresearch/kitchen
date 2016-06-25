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

Recommend recipes.
"""
import sys, os, argparse, time
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from recipes.recipe_handler import *
from utils.general_utils import *

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--recipes", help="Input recipe file.", default=ALLRECIPES_DICT)
    parser.add_argument("--keywords", help="Keywords.", nargs='*', default=[])
    parser.add_argument("--ingredients", help="Ingredients.", nargs='*', default=[])
    parser.add_argument("--sortby", help="Sortby method(s).", nargs='*', default=["relevance", "popular", "rating"])
    args = parser.parse_args()

    handler = RecipeHandler()
    t = time.time()
    rids = handler.getRecipeIds(args.ingredients, args.keywords, args.sortby)
    print time.time()-t
    #data = convertToStrings(handler.getRecipeData(rids))
    #print data
    #for row in data:
    #    print row["title"], row["made-it"]
