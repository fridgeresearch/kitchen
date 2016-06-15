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

Parse recipes crawled from allrecipes.com and output data structures.
"""
import sys, os, argparse, json, multiprocessing
from bs4 import BeautifulSoup
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

def parseRecipe(args):
    fpath, recipes = args
    rid = splitext(basename(fpath))[0]
    url, data = open(fpath).read().split('\n', 1)
    url = url.strip()
    print url
    soup = BeautifulSoup(data)
    r = {}
    r["url"] = url
    r["title"] = soup.html.head.title.text.replace(" - Allrecipes.com", "").strip()
    summary = soup.find("section", {"class":"recipe-summary"})
    r["rating"] = float(summary.find("div", {"class":"rating-stars"})["data-ratingstars"])
    r["made-it"] = int(summary.find("div", {"class":"total-made-it"})["data-ng-init"].\
                       replace("init(","").strip(")"))
    cats = [v.text.strip() for v in soup.find("li", {"title":"Categories"}).findAll("h3")]
    r["categories"] = list(set(cats))
    mdesc = soup.find("meta", {"id":"metaDescription"})["content"].strip()
    r["meta-description"] = mdesc
    ingreds = [v.text.strip() for v in soup.findAll("span", {"itemprop":"ingredients"})]
    r["ingredients"] = list(set(ingreds))
    pics = soup.find("a", {"title":"See Recipe Pictures"})
    if pics != None:
        pid = basename(pics["href"].strip("/"))
        r["image-url"] = "http://images.media-allrecipes.com/userphotos/250x250/%s.jpg"%pid
    else:
        r["image-url"] = None
    r["nutrition"] = dict([(v["itemprop"], v.text) for v in \
                           soup.findAll("li", {"class":"nutrientLine__item--amount"})])
    r["directions"] = [v.text for v in soup.findAll("span", {"class":"recipe-directions__list--item"})\
                       if v.text]
    try:
        r["ready-in-time"] = soup.find("span", {"class":"ready-in-time"}).text
    except Exception as e:
        r["ready-in-time"] = None
    try:
        r["servings"] = int(soup.find("meta", {"id":"metaRecipeServings"})["content"].strip())
    except Exception as e:
        r["servings"] = None
    recipes[rid] = r
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--input", help="Input data dir.", default=ALLRECIPES_DATA)
    parser.add_argument("--output", help="Output json file.", default=ALLRECIPES_DICT)
    args = parser.parse_args()

    fpaths = [join(d, f) for (d, _, fs) in os.walk(args.input) \
              for f in fs if splitext(f)[1]==".html"]
    """
    d = {}
    for f in fpaths[100:400]: parseRecipe((f, d))
    sys.exit(0)
    """
    m = multiprocessing.Manager()
    d = m.dict()
    p = multiprocessing.Pool()
    p.map(parseRecipe, zip(fpaths, [d]*len(fpaths)))
    json.dump(dict(d), open(args.output, "w"), sort_keys=True, indent=2, separators=(',', ': '))
