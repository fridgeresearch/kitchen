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

Program to crawl allrecipes.com.
Crawler logic implemented by Crawler class.
State maintenance implemented by CrawlerState class.
"""
import sys, os, argparse, urllib2, pickle, json, select
from bs4 import BeautifulSoup
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from utils.logging_utils import *

queue, visited = [], []

class CrawlerState:
    """Class for maintaining crawler state.
    
    Attributes:
        queue: Queue of urls to visit.
        visited: List of urls visited.
        visiting: List of urls currently visiting.
    """    
    def __init__(self):
        """Initialize state (everything null)."""
        self.queue, self.visited, self.visiting = [], [], []
    def reinit(self):
        """Reinitialize state by moving visiting contents to queue."""
        self.queue += self.visiting
        self.visiting = []
    def put(self, url, data=None):
        """Queue the url and data (if provided).
        
        Places a (url, data) pair in the queue. Data goes at the front
            if photo data and at the back otherwise.
        
        Args:
            url: url to queue.
            data: optional additional data associated with url.
        """
        crawler_data = (url, data)
        if crawler_data not in self.queue + self.visited + self.visiting:
            logging.debug("Queueing %s." % url)
            if "/photos/" in url or ".jpg" in url:
                self.queue.insert(0, crawler_data)
            else:
                self.queue.append(crawler_data)
    def get(self):
        """Removes data from the queue, adds it to visiting, and returns."""
        crawler_data = self.queue[0]
        self.queue = self.queue[1:]
        self.visiting.append(crawler_data)
        return crawler_data
    def mark(self, url, data=None):
        """Mark the url as visited.
        
        Removes url from visiting and places in visited.
        
        Args:
            url: url previously queued and removed.
            data: data previously queued and removed.
        """
        crawler_data = (url, data)
        self.visiting.remove(crawler_data)
        self.visited.append(crawler_data)
    def started(self):
        """Returns whether or not crawl has started."""
        return len(self.queue + self.visited + self.visiting) > 0
    def done(self):
        """Returns if crawl is done."""
        return not self.queue

class Crawler:
    """Class for implementing crawler logic.
    
    Attributes:
        state: CrawlerState object.
        base_url: allrecipes.com url.
        data_dir: directory for data.
        state_fname: filename for state.
    """    
    def __init__(self, output):
        """Initialize the crawler with null state and output vars.
        
        Args:
            output: output stem (output directory).
        """
        self.state = CrawlerState()
        self.base_url = "http://allrecipes.com"
        self.data_dir = output
        self.state_fname = "%s.pkl"%output
    def loadState(self):
        """Loads the crawler state."""
        if exists(self.state_fname):
            self.state = pickle.load(open(self.state_fname, "r"))
            self.state.reinit()
    def saveState(self):
        """Saves the crawler state."""
        pickle.dump(self.state, open(self.state_fname, "w"))
    def crawlRecipesGroups(self, read):
        """Crawls recipes groups soup.
        
        Adds all recipes groups to the crawler state.
        
        Args:
            read: Data read from url."""
        soup = BeautifulSoup(read)
        filter_dict = {"class":"grid ng-hide", "ng-show":"showAll===true"}
        for r in soup.find("div", filter_dict).findAll("a"):
            self.state.put(self.base_url+r["href"]+"?page=1")
    def crawlRecipes(self, url, soup):
        """Crawls recipes.
        
        For a given recipes page / soup, add all recipes and the next page.
        
        Args:
            url: Recipes url.
            soup: Recipes soup."""
        # Queue individual recipes.
        done = True
        for r in soup.findAll("article", {"class":"grid-col--fixed-tiles"}):
            if len(r["class"]) > 1: continue
            recipe_url = self.base_url + r.find("a")["href"]
            if recipe_url not in queue and recipe_url not in visited:
                done = False
                self.state.put(recipe_url)
        # Queue group page.
        if not done:
            page = int(url.split("=")[-1])
            recipes_url = url.rsplit("=",1)[0] + "=" + str(page+1)
            self.state.put(recipes_url)
    def crawlRecipe(self, url, read, soup, crawl_photos):
        """Crawls recipe.
        
        For a given recipe page / soup, save metadata and add photos url to state.
        
        Args:
            url: Recipe url.
            read: Data read from url.
            soup: Recipe soup."""
        recipe_html = self._recipeDirectory(url).rstrip("/") + ".html"
        if not exists(dirname(recipe_html)):
            os.makedirs(dirname(recipe_html))
        open(recipe_html, "w").write(url+read)
        pics = soup.find("a", {"title":"See Recipe Pictures"})
        if crawl_photos and pics:
            self.state.put(self.base_url + pics["href"])
            
    def crawlRecipePhotos(self, url, read, soup, crawl_photos):
        """Crawls recipe photos.
        
        For a given recipe photos page, add all image urls & data to state.
        
        Args:
            url: Recipe photos url.
            read: Data read from url.
            soup: Recipe photos soup."""
        recipe_base = self._recipeDirectory(url).rstrip("/")
        recipe_url_fname = recipe_base + "-photos.html"
        open(recipe_url_fname, "w").write(url+"\n"+read)
        # For each photo, download the photo in available dimensions.
        max_photos = 10
        for r in soup.find("ul", {"class":"photos--band"}).findAll("img")[:max_photos]:
            for shape in ["250x250", "600x600", "720x405"]:
                url_im = r["src"].replace("250x250", shape)
                if crawl_photos: self.state.put(url_im, recipe_base+"/")

    def saveRecipePhoto(self, url, im_data, recipe_dir):
        """Saves recipe photo.
        
        Parses the url and uses the recipe directory to get the output path.
            Writes the im_data to that path.
        
        Args:
            url: Recipe photo url.
            im_data: Image data to write.
            recipe_dir: Recipe output directory."""
        im_id = splitext(basename(url))[0]
        shape = basename(dirname(url))
        if not exists(recipe_dir): os.makedirs(recipe_dir)
        open(join(recipe_dir, "%s-%s.jpg"%(im_id, shape)), "w").write(im_data)
    def crawl(self, crawl_photos):
        """Crawl allrecipes.com.
        
        Crawls allrecipes.com in a depth-first fashion:
           (recipes -> recipe -> recipe photos -> photo).
           For each of those cases, calls appropriate parsing / saving function.
        """
        if not self.state.started():
            read = self._urlRead(self.base_url+"/recipes/?grouping=all")
            self.crawlRecipesGroups(read) # init with recipes from groups.
        while not self.state.done():
            r = select.select([sys.stdin], [], [], 0.1)[0]
            if r and sys.stdin.readline()[:-1] == 'q': break
            (url, data) = self.state.get()
            logging.info("Visiting %s." % url)
            try:
                read = self._urlRead(url)
            except Exception as e:
                logging.warning("Warning '%s' for url %s" % (str(e), url))
                continue
            if ".jpg" in url:
                if crawl_photos:
                    self.saveRecipePhoto(url, read, data)
                else:
                    logging.warning("Trying to saveRecipePhoto at %s" % url)
            else:
                soup = BeautifulSoup(read)
                if ".com/recipes/" in url:
                    self.crawlRecipes(url, soup)
                elif ".com/recipe/" in url and "/photos/" in url:
                    if crawl_photos:
                        self.crawlRecipePhotos(url, read, soup, crawl_photos)
                    else:
                        logging.warning("Trying to crawlRecipePhoto at %s" % url)
                elif ".com/recipe/" in url:
                    self.crawlRecipe(url, read, soup, crawl_photos)
            self.state.mark(url, data) # mark as visited if successful
    def _urlRead(self, url, max_attempts=5):
        """Helper function to read data from specified url.
        
        Reads data from specified url. Will try max_attempts times before giving
           up and throwing an exception.

        Args:
            url: Url to read.
            max_attempts: Number of times to try before giving up.
        """
        for attempt in range(max_attempts):
            request = urllib2.Request(url)
            try:
                response = urllib2.urlopen(request, timeout=5.0)
                return response.read()
            except Exception as e:
                if attempt == max_attempts-1:
                    raise e
    def _recipeDirectory(self, url):
        """Helper function to construct recipe directory from url.
        
        Extracts the recipe ID from the url and uses it to construct directory.

        Args:
            url: Url to parse to construct recipe directory.
        """
        rid = url.replace(self.base_url+"/recipe/", "").split("/")[0]
        return join(self.data_dir, rid[0], rid[1], rid)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='allrecipes.com crawling.')
    parser.add_argument("--output", help="Output stem.", default=ALLRECIPES_DATA)
    parser.add_argument("--crawl-photos", help="Crawl recipe photos.")
    args = parser.parse_args()

    configureLogging("%s.log" % args.output.rstrip("/"))
    crawler = Crawler(args.output)
    crawler.loadState()
    try:
        crawler.crawl(args.crawl_photos)
    except Exception as e:
        handleException("main", e)
    crawler.saveState()
    
