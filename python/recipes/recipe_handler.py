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
"""
import sys, os, json, time, logging, inspect
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *

class RecipeHandler():
    """Class for handling recipes.

    Attributes:
        recipes: Dictionary from recipe ID to recipe data.
    """
    def __init__(self, recipes=ALLRECIPES_DICT, search_ingredients=SEARCH_INGREDIENTS):
        """Initialize handler.
        
        Initialize the handler. Loads the recipe data structure.
        
        Args:
            recipes: Path to recipes data structure.
            food_hash: Hash from food name to tags and to recipes containing that food.
            adj: Adjacency matrix for recipes and ingredients.
            sortby_methods: Valid sortby methods."""
        self.recipes = json.loads(open(recipes).read())
        for (k, v) in json.loads(open(IDEORECIPES_DICT).read()).items():
            self.recipes[k] = v
        self.search_ingredients = [v.strip().lower() for v in open(search_ingredients)]
        self.food_hash = {}
        self.adj = None
        self.sortby_methods = ["relevance", "popular", "rating"]
        self.to_skips = ["sugar", "salt", "milk", "pepper", "butter"]

    def updateFoodHash(self, ingredients):
        func_name = inspect.stack()[0][3]
        logging.debug('%s', func_name)
        for (i, (food_name, food_tags)) in enumerate(ingredients.items()):
            food_tags = [v.lower() for v in food_tags]
            if food_name not in self.food_hash or \
               sorted(self.food_hash[food_name]["tags"]) != sorted(food_tags):
                logging.debug('%s Updating for %s (%d of %d)', func_name, food_name,
                              i+1, len(ingredients.keys()))
                self.food_hash[food_name] = {
                    "tags": food_tags,
                    "rids": set([rid for (rid, recipe) in self.recipes.items() if \
                                 any(any(tag.lower() in recipe_food.lower() for tag in food_tags) \
                                     for recipe_food in recipe["ingredients"])])
                }

    def setAdjacencyMatrix(self):
        func_name = inspect.stack()[0][3]
        logging.debug('%s computing adjacency matrix...', func_name)
        self.adj = np.array([[any(ingredient in v for v in recipe["ingredients"]) \
                              for ingredient in self.search_ingredients] \
                             for recipe in self.recipes.values()])
        logging.debug('%s done computing adjacency matrix...', func_name)
    
    def split(self, previous_splits):
        if self.adj==None: self.setAdjacencyMatrix()
        idx = np.arange(self.adj.shape[0])
        for (split_ftr_name, yes_no) in previous_splits:
            split_ftr_idx = self.search_ingredients.index(split_ftr_name)
            #if yes_no:
            #    idx = idx[np.nonzero(self.adj[idx, split_ftr_idx])]
            #else:
            if not yes_no:
                idx = idx[np.nonzero(1-self.adj[idx, split_ftr_idx])]
        y = 1.0 * np.sum(self.adj[idx, :], axis=0) / len(idx)
        to_skips = self.to_skips + [v[0] for v in previous_splits]
        y = np.array([0.0 if any(w in self.search_ingredients[i] for w in to_skips) else v\
                      for (i, v) in enumerate(y)])
        split_ftr_idx = np.argmin(abs(0.5-y))
        return self.search_ingredients[split_ftr_idx]
    
    def getRecipes(self, keywords=[], 
                   all_ingredients={}, include_ingredients={}, exclude_ingredients={},
                   sortby=["relevance", "popular"],
                   cols=None, per_page=None, page=None):
        """Get recipes.
        
        Return recipes given list of ingredients and/or keywords.
        
        Args:
            {all, include, exclude}_ingredients: dictionaries from ingredient names to ingredient tags.
            keywords: Relevant keywords.
            sortby: Sorting method(s) (popular, rating, or relevance).
            cols: Recipe columns."""
        include_ingredients = dict([(k, [w.lower() for w in v]) \
                                    for (k, v) in include_ingredients.items()])
        keywords = list(set([v.lower() for v in keywords]))
        self.updateFoodHash(include_ingredients)
        self.updateFoodHash(exclude_ingredients)
        # Get dictionary from recipe ID to sorting scores.
        result = []
        for (rid, recipe) in self.recipes.items():
            if any([rid in self.food_hash[v]["rids"] \
                    for v in exclude_ingredients.keys()]): continue
            matched_include = [v for v in include_ingredients.keys() if rid in self.food_hash[v]["rids"]]
            missing_include = [v for v in include_ingredients.keys() if v not in matched_include]
            #matched_all = [v for v in all_ingredients.keys() if rid in self.food_hash[v]["rids"]]
            #missing_all = [v for v in all_ingredients.keys() if rid in self.food_hash[v]["rids"]]
            recipe_keywords = recipe["title"].lower() + " ".join(recipe["categories"])
            relevance = sum([v in recipe_keywords for v in keywords])
            if not keywords or relevance:
                scores = [len(matched_include)]
                for method in sortby:
                    if method=="relevance":
                        scores.append(relevance)
                    elif method=="popular":
                        scores.append(float(self.recipes[rid]["made-it"]))
                    elif method=="rating":
                        scores.append(float(self.recipes[rid]["rating"]))
                    else:
                        raise Exception('sortby parameter unrecognized: "%s".' % method)
                copy_cols = [v for v in cols] if cols else self.recipes[rid].keys()
                d = {}
                for col in copy_cols:
                    d[col] = self.recipes[rid][col]
                d["missing_include_ingredients"] = missing_include
                d["id"] = rid
                result.append((tuple(scores), d))
        # Sort results and extract range
        result = [v[1] for v in sorted(result, key=lambda x: x[0])][::-1]
        if per_page!=None and page!=None:
            result = result[per_page*(page-1):per_page*page]
        return result

directions = [
    "In a dutch oven, cook \\ingredient{sausage}, \\ingredient{ground beef}, \\ingredient{onion}, and \\ingredient{garlic} over medium heat until well browned",
    "Stir in \\ingredient{crushed tomatoes}, \\ingredient{tomato paste}, \\ingredient{tomato sauce}, and \\ingredient{water}.",
    "Season with \\ingredient{sugar}, \\ingredient{basil}, \\ingredient{fennel seeds}, \\ingredient{Italian seasoning}, 1 tablespoon \\ingredient{salt}, \\ingredient{pepper}, and 2 tablespoons \\ingredient{parsley}.",
    "Simmer, covered, for about 1 1/2 hours, stirring occasionally.",
    "Bring a large pot of lightly salted \\ingredient{water} to a boil.",
    "Cook \\ingredient{lasagna noodles} in boiling water for 8 to 10 minutes.",
    "Drain \\ingredient{noodles}, and rinse with cold water. In a mixing bowl, combine \\ingredient{ricotta cheese} with \\ingredient{egg}, remaining \\ingredient{parsley}, and 1/2 teaspoon \\ingredient{salt}.",
    "Preheat oven to 375 degrees F (190 degrees C).",
    "To assemble, spread 1 1/2 cups of meat sauce in the bottom of a 9x13 inch baking dish.",
    "Arrange 6 \\ingredient{noodles} lengthwise over meat sauce. Spread with one half of the ricotta cheese mixture.",
    "Top with a third of \\ingredient{mozzarella cheese slices}.",
    "Spoon 1 1/2 cups meat sauce over \\ingredient{mozzarella}, and sprinkle with 1/4 cup \\ingredient{Parmesan cheese}.",
    "Repeat layers, and top with remaining \\ingredient{mozzarella} and \\ingredient{Parmesan cheese}.",
    "Cover with foil: to prevent sticking, either spray foil with cooking spray, or make sure the foil does not touch the cheese."
]
