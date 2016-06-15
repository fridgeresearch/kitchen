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
import sys, os, unittest, json, urllib2, requests
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from api.app_api import *

class TestStringMethods(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        config = json.loads(open(API_CONFIG).read())
        self.base_url = "http://serverkitchen.duckdns.org/appapi/v2/"
        self.server = ServerWrapper(config["host"], config["port"], config["db"],
                                   config["db-user"], config["db-passwd"], config["db-host"])
        self.server.serve()

    @classmethod
    def tearDownClass(self):
        self.server.shutdown()

    def test_postGroceryBundles(self):
        # Test posting GroceryBundles.
        #data = requests.ppost(self.base_url+"/groceryBundles?TODO)

    def test_putGroceryBundles(self):
        # Test putting GroceryBundles.
        #data = requests.put(self.base_url+"/groceryBundles?TODO)

    def test_deleteInventory(self):
        # Test deleting ItemRead's from Inventory.
        #data = requests.put(self.base_url+"/inventory?1,2,3")
    def test_getPhotos(self):
        # Test photos.
        # TODO.

    def test_getFood(self):
        # Test existing Food.
        data = self._urlRead(self.base_url+"/foods/6")
        r = json.loads(data)
        self.assertEqual(r["food_id"], 6)
        self.assertEqual(r["food_image_url"], None)
        self.assertEqual(r["food_life"], None)
        self.assertEqual(r["food_name"], "Whole Foods Artichoke Lemon Spread")
        self.assertEqual(r["foodtype_id"], None)
        self.assertEqual(r["foodtype_image_url"], None)
        self.assertEqual(r["foodtype_life"], None)
        self.assertEqual(r["foodtype_name"], None)
        # Test non-existant Food.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Food{id:0} Not Found.'):
            self._urlRead(self.base_url+"/foods/0")
        # Test bad food-id.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Invalid Food.id=a.'):
            self._urlRead(self.base_url+"/foods/a")

    def test_getInventory(self):
        # Test inventory.
        data = self._urlRead(self.base_url+"/inventory")
        r = json.loads(data)
        self.assertEqual(len(r), 29)
        d = {u'food_description': None, u'weight': 479.741, 
             u'food_name': u'Clover Heavy Whipping Cream - 1 Pint',
             u'food_id': 33, u'initial_time': u'20160106T044313.659811',
             u'initial_weight': 479.741, u'food_image_url': None}
        self.assertEqual(r[0], d)
        d = {u'food_description': None, u'weight': 87.4662,
             u'food_name': u'Lucerne 2% Milk American Cheese Slices',
             u'food_id': 15, u'initial_time': u'20160106T044758.516585',
             u'initial_weight': 165.012, u'food_image_url': None}
        self.assertEqual(r[-1], d)
        # Test inventory with additional illegal args.
        with self.assertRaisesRegexp(urllib2.HTTPError, "Invalid GET path."):
            self._urlRead(self.base_url+"/inventory/0")

    def test_getRecipes(self):
        base = self.base_url + "/recipes?"
        args = "ingredients=mayonnaise&keywords=corn&sortby=rating&per_page=20&page=2"
        url = base + args
        # Test recipes.
        data = self._urlRead(url)
        r = json.loads(data)
        self.assertEqual(len(r), 20)
        self.assertEqual(r[0]["title"], "Mexican Street Vendor Style Corn Salad Recipe")
        self.assertEqual(r[-1]["title"], "Caribbean Corn and Apple Salad Recipe")
        # Test no arguments.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Recipes requires arguments.'):
            self._urlRead(base[:-1])
        # Test non-key-value pair.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Recipes requires key-value pairs.'):
            self._urlRead(base+"0")
        # Test missing key.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Recipes arguments must be*'):
            self._urlRead(url.replace("per_page=20&", ""))
        # Test unknown key
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Recipes arguments must be*'):
            self._urlRead(url.replace("per_page", "per_pages"))
        # Test per_page / page argument length != 1.
        with self.assertRaisesRegexp(urllib2.HTTPError, '.*exactly one.*'):
            self._urlRead(url.replace("&per_page=20", "&per_page="))
        with self.assertRaisesRegexp(urllib2.HTTPError, '.*exactly one.*'):
            self._urlRead(url.replace("&page=2", "&page=2,3"))
        # Test non-int amd out-of-bounds per_page.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Invalid per_page=a.'):
            self._urlRead(url.replace("&per_page=20", "&per_page=a"))
        # Test out-of-bounds per_page.
        err_msg = 'per_page must be in \[1, 100\].'
        with self.assertRaisesRegexp(urllib2.HTTPError, err_msg):
            self._urlRead(url.replace("&per_page=20", "&per_page=0"))
        with self.assertRaisesRegexp(urllib2.HTTPError, err_msg):
            self._urlRead(url.replace("&per_page=20", "&per_page=1000"))
        # Test non-int amd out-of-bounds page.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Invalid page=a.'):
            self._urlRead(url.replace("&page=2", "&page=a"))
        # Test out-of-bounds page.
        err_msg = 'page must be >= 1.'
        with self.assertRaisesRegexp(urllib2.HTTPError, err_msg):
            self._urlRead(url.replace("&page=2", "&page=0"))
        # Test unknown sortby method.
        err_msg = "Recipe sortby method\(s\) \['foo'\] not in.*"
        with self.assertRaisesRegexp(urllib2.HTTPError, err_msg):
            self._urlRead(url.replace("rating", "foo"))
        
    def test_getGroceryList(self):
        # Test current and specific grocery lists.
        for args in ["/groceryList", "/groceryList/2"]:
            data = self._urlRead(self.base_url + args)
            r = json.loads(data)
            self.assertEqual(len(r), 2)
            self.assertEqual(r[0]["food_name"], "Daisy Sour Cream - 16 Oz")
            self.assertEqual(r[-1]["food_name"], "Noah's Double Whipped Plain Shmear")
        # Test non-existant GroceryList.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'GroceryList{id:0} Not Found.'):
            self._urlRead(self.base_url+"/groceryList/0")
        # Test bad GroceryList.id.
        with self.assertRaisesRegexp(urllib2.HTTPError, 'Invalid GroceryList.id=a.'):
            self._urlRead(self.base_url+"/groceryList/a")

    def _urlRead(self, url, max_attempts=1):
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
                print e
                if attempt == max_attempts-1:
                    raise e

if __name__ == "__main__":
    unittest.main()
