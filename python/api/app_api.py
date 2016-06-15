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

App server.
"""

import sys, os, argparse, json, base64, inspect, threading, requests
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from db.db_handler import *
from recipes.recipe_handler import *
from utils.logging_utils import *
from utils.general_utils import *
from api.common import *

class AppServerWrapper(ServerWrapper):
  def __init__(self, host, port, db, user, passwd, dbhost, ble_url, init_handler):
    func_name = inspect.stack()[0][3]
    logging.info('%s', func_name)
    def handlerInit(*args):
      AppHandler(db, user, passwd, dbhost, ble_url, init_handler, *args)
    ServerWrapper.__init__(self, host, port, handlerInit)
    # Initialize Handler for the first time automatically.
    AppHandler(db, user, passwd, dbhost, ble_url, init_handler)

class AppHandler(Handler):
  """Processes HTTP requests for app.

  Class attributes:
      recipe_handler: RecipeHandler.
      db: Database name.
      user: Database username.
      passwd: Database password.
  """
  recipe_handler = RecipeHandler()
  db, user, passwd, host = None, None, None, None
  def __init__(self, db, user, passwd, host, ble_url, init_handler, *args):
    self.ble_url = ble_url
    self.uid, self.username = None, None
    Handler.__init__(self, *args)
    if AppHandler.db == None:
      AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host = db, user, passwd, host
      if init_handler:
        self._updateFoodHash()
        #AppHandler.recipe_handler.setAdjacencyMatrix()
  
  def _updateFoodHash(self):
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    food_hash = db_handler.getFoodTagHash()
    AppHandler.recipe_handler.updateFoodHash(food_hash)
    """
    ingredients = {}
    for food in db_handler.get(["Food"]):
      tags = sorted([v["FoodTag.name"] for v in db_handler.getFoodTags(food["Food.id"])])
      ingredients[food["Food.name"]] = tags
    AppHandler.recipe_handler.updateFoodHash(ingredients)
    """

  def _getCurrentGroceryListId(self, db_handler):
    constraints = ["GroceryList.kitchen_id=%d"%self.uid,
                   "GroceryList.time_done is NULL"]
    gids = db_handler.get(["GroceryList"], constraints=constraints)
    if len(gids) > 1:
      raise Exception("multiple incomplete grocery lists for kitchen %d."%self.uid)
    if gids:
      return gids[0]["GroceryList.id"]
    else:
      t_str = dateTimeToTimeString(datetime.datetime.utcnow())
      db_handler.insert("GroceryList", {"kitchen_id":self.uid, "time_created":t_str})
      db_handler.commit()
      return db_handler.lastRowId()

  def checkAuth(self):
    func_name = inspect.stack()[0][3]
    """Check the supplied credentials (username and password) for HTTP basic
    authentication.

    """
    self.uid = None
    if self.headers.getheader('Authorization') == None:
      self.do_AUTHHEAD()
      logging.error('%s Not authorized', func_name)
      return False
    else:
      key_provided = self.headers.getheader('Authorization').split()[1]
      key_decoded = base64.b64decode(key_provided)
      key_parts = key_decoded.split(':')
      u_provided = key_parts[0]
      p_provided = key_parts[1]
      db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
      r = db_handler.checkAuth(u_provided, p_provided)
      logging.info('%s checkAuth result=%s', func_name, str(r))
      if r != None:
        self.uid = r["Kitchen.id"]
        self.username = r["Kitchen.name"]
        return True
      else:
        self.uid, self.username = None, None
        self.sendError(403, caller=func_name)
        return False

  def do_POST(self):
    func_name = inspect.stack()[0][3]
    try:
      if not self.checkAuth():
        return
      logging.info('%s path=%s', func_name, self.path)
      pathparts = self.path.split('/')
      if len(pathparts) == 2 and pathparts[1].split('?')[0] == 'groceryBundles': # /groceryBundles?
        self.processGroceryBundles(pathparts)
      elif len(pathparts) == 2 and pathparts[1] == 'groceryOrder': # /groceryOrder
        bundles = self.processGetGroceryList(pathparts, mark_done=True)
        self.sendData(None)
      elif len(pathparts) == 2 and pathparts[1].split('?')[0] == 'containerAnimation': # /containerAnimation?
        self.processContainerAnimation(pathparts)
    except Exception, e:
      handleException(func_name, e)
      self.sendError(500, caller=func_name)

  def _bundleHelper(self, db_handler, pathparts, keys):
    func_name = inspect.stack()[0][3]
    gid = self._getCurrentGroceryListId(db_handler)
    d = self._extractDict(pathparts, keys, "GroceryBundles", func_name)
    if d == None: return None
    lens = list(set([len(v) for v in d.values()]))
    if len(lens) > 1:
      self.sendError(400, message="Misalinged GroceryBundle keys.", caller=func_name)
      return None
    bundles = [dict([("grocery_list_id",gid)] + [(k, d[k][i]) for k in keys]) \
               for i in range(lens[0])]
    return bundles

  def getBeaconAddrs(self, item_ids):
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    irs = [v for v in db_handler.getPresentItemReads(kitchen_id=self.uid) if v["Item.id"] in item_ids]
    bstr = "Beacon.address"
    return dict([(v["Item.id"], v[bstr] if bstr in v else None) for v in irs])

  def processContainerAnimation(self, pathparts):
    func_name = inspect.stack()[0][3]
    d = self._extractDict(pathparts, None, "containerAnimation", func_name)
    if d == None: return None
    if "item_ids" not in d or "animation" not in d:
      self.sendError(400, message="containerAnimation requires item_ids and animation.", caller=func_name)
      return None
    iids = map(int, d["item_ids"])
    addr_map = self.getBeaconAddrs(iids)
    data = {"addrs": [v for v in addr_map.values() if v!=None]}
    for (k, v) in d.items():
      if k not in ["item_ids", "animation"]: data[k] = v
    url = self.ble_url + "/" + d["animation"] + '?' + json.dumps(data)
    auth = ""
    data = requests.post(url, headers={"Authorization":auth})
    self.sendData(None)

  def processGroceryBundles(self, pathparts):
    func_name = inspect.stack()[0][3]
    t_str = dateTimeToTimeString(datetime.datetime.utcnow())
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    bundles = self._bundleHelper(db_handler, pathparts, ["food_name", "quantity"])
    # Insert any foods that aren't already in the database.
    names = [v["food_name"] for v in bundles]
    existing_names = set([v["Food.name"] for v in db_handler.get(["Food"])])
    new_names = set(names).difference(existing_names)
    db_handler.insertMany("Food", [{"name": v} for v in new_names])
    # Fetch GroceryItems and add / remove items to match bundle sizes.
    constraints = ["GroceryItem.food_id=Food.id",
                   "Food.name in (%s)" % ','.join(['"%s"'%v for v in names]),
                   "GroceryItem.time_removed is NULL"]
    items = db_handler.get(["GroceryItem", "Food"], constraints=constraints)
    for bundle in bundles:
      name = bundle["food_name"]
      bundle_items = [v for v in items if v["Food.name"]==name]
      bundle_qty = bundle["quantity"]
      delta = bundle_qty - len(bundle_items)
      if delta < 0:
        removal_items = sorted(bundle_items, key=lambda x: x["GroceryItem.time_added"])[delta:]
        for item in removal_items:
          db_handler.update("GroceryItem", {"time_removed":t_str}, \
                            constraints=["GroceryItem.id=%d"%item["GroceryItem.id"]])
      elif delta > 0:
        item = {"grocery_list_id":bundles[0]["grocery_list_id"], "time_added":t_str}
        fid = db_handler.get(["Food"], constraints=['Food.name="%s"'%name])
        if fid:
          item["food_id"] = fid[0]["Food.id"]
          db_handler.insertMany("GroceryItem", [item]*delta)
    db_handler.commit()
    self.sendData(None)

  def do_DELETE(self):
    func_name = inspect.stack()[0][3]
    try:
      if not self.checkAuth():
        return
      logging.info('%s path=%s', func_name, self.path)
      pathparts = self.path.split('/')
      if len(pathparts) == 2 and pathparts[1].split('?')[0] == 'inventory': # /inventory?
        self.processDeleteInventory(pathparts)
    except Exception, e:
      handleException(func_name, e)
      self.sendError(500, caller=func_name)
  
  def processDeleteInventory(self, pathparts):
    func_name = inspect.stack()[0][3]
    if '?' not in pathparts[1]:
      self.sendError(400, message="requires arguments.", caller=func_name)
      return
    d = self._extractDict(pathparts, ["ids"], "Inventory", func_name)
    if d == None: return None
    self.deleteInventory(d["ids"])
    
  def deleteInventory(self, ids):
    func_name = inspect.stack()[0][3]
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    constraints = ["id in (%s);" % ','.join(map(str,ids))]
    db_handler.delete("ItemRead", constraints=constraints)
    db_handler.commit()
    logging.info("%s Deleted with constraints=%s", func_name, str(constraints))
    self.sendData(None)

  def do_GET(self):
    func_name = inspect.stack()[0][3]
    try:
      if not self.checkAuth():
        return
      logging.info('%s path=%s', func_name, self.path)
      pathparts = self.path.split('/')

      if len(pathparts) == 2 and pathparts[1] == 'photos': # /photos
        self.getPhotos()
      elif len(pathparts) == 2 and pathparts[1].split('?')[0] == 'containerWeights': # /containerWeights?
        self.processContainerWeights(pathparts)
      elif len(pathparts) == 3 and pathparts[1] == 'foods': # /foods
        self.processGetFood(pathparts)
      elif 2 <= len(pathparts) <= 3 and pathparts[1] == 'groceryList': #/groceryList
        bundles = self.processGetGroceryList(pathparts)
        self.sendData(bundles)
      elif len(pathparts) == 2 and pathparts[1] == 'inventory': # /inventory
        self.getInventory()
      elif len(pathparts) == 2 and pathparts[1].split('?')[0] == 'recipes': # /recipes?
        self.processGetRecipes(pathparts)
      elif len(pathparts) == 2 and pathparts[1].split('?')[0] == 'split': # /split?
         self.processGetSplit(pathparts)      
      else:
        self.sendError(400, message="Invalid GET path.", caller=func_name)
    except Exception, e:
      handleException(func_name, e)
      self.sendError(500, caller=func_name)

  def processContainerWeights(self, pathparts):
    func_name = inspect.stack()[0][3]
    d = self._extractDict(pathparts, ["item_ids"], "containerWeights", func_name)
    if d == None: return None
    iids = map(int, d["item_ids"])
    iid_to_addr = self.getBeaconAddrs(iids)
    data = {"addrs": iid_to_addr.values()}
    url = self.ble_url + "/weights?" + json.dumps(data)
    auth = ""
    addr_to_wt = requests.get(url, headers={"Authorization":auth}).json()
    #data = dict([(k, v) for (k, v) in zip(iids, wts) if v != None])
    wts = [addr_to_wt[iid_to_addr[v]] for v in iids]
    data = dict([(k, v) for (k, v) in zip(iids, wts) if v != None])
    self.sendData(data)

  def getPhotos(self):
    func_name = inspect.stack()[0][3]
    kitchen_dir = join(args.data, "Kitchen%07d"%self.uid)
    snap_dir = join(kitchen_dir, "Snapshots")
    snap_ims = [v for v in os.listdir(snap_dir) if "270x480" in v]
    if not snap_ims:
      self.sendError(404, message='No images found.', caller=func_name)
    else:
      event_id = int(sorted(snap_ims)[-1].replace("Snapshot", "").split("-")[0])
      fnames = [join(snap_dir.replace(PARENT_DIR, ""), v) for v in snap_ims \
                if "Snapshot%06d"%event_id in v]
      self.sendData(fnames)

  def processGetGroceryList(self, pathparts, mark_done=False):
    func_name = inspect.stack()[0][3]
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    if len(pathparts) == 3:
      try:
        gid = int(pathparts[2])
      except Exception as e:
        self.sendError(400, message="Invalid GroceryList.id=%s."%pathparts[2], caller=func_name)
        return
      if not db_handler.get(["GroceryList"], constraints=["GroceryList.id=%d"%gid]):
        self.sendError(404, message='GroceryList{id:%d} Not Found.'%gid, caller=func_name)
        return
    else:
      gid = self._getCurrentGroceryListId(db_handler)
    func_name = inspect.stack()[0][3]
    constraints = ["GroceryList.id=%d"%gid,
                   "GroceryList.kitchen_id=%d" % self.uid,
                   "GroceryItem.grocery_list_id=GroceryList.id",
                   "GroceryItem.food_id=Food.id"]
    items = db_handler.get(["Food", "GroceryList", "GroceryItem"],
                           constraints=constraints)
    names = set([v["Food.name"] for v in items])
    bundles = []
    for name in names:
      bundle_items = [v for v in items if v["Food.name"]==name]
      bundle_time = [v["GroceryItem.time_added"] for v in bundle_items]
      active_bundle_items = [v for v in bundle_items if not v["GroceryItem.time_removed"]]
      if active_bundle_items:
        bundles.append({"food_name":name, "quantity":len(active_bundle_items), "t": bundle_time})
    bundles = sorted(bundles, key=lambda x: x["t"], reverse=True)
    for b in bundles: del b["t"]
    logging.info("%s data=%s", func_name, str(bundles))
    if mark_done:
      t_str = dateTimeToTimeString(datetime.datetime.utcnow())
      db_handler.update("GroceryList", {"time_done":t_str}, \
                        constraints=["GroceryList.id=%d"%gid])
      db_handler.commit()
    return bundles

  def processGetFood(self, pathparts):
    func_name = inspect.stack()[0][3]
    try:
      fid = int(pathparts[2])
    except Exception as e:
      self.sendError(400, message="Invalid Food.id=%s."%pathparts[2], caller=func_name)
      return
    self.getFood(fid)

  def getFood(self, fid):
    func_name = inspect.stack()[0][3]
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    foods = db_handler.get(["Food"], constraints=["Food.id=%d"%fid])
    if foods:
      food = foods[0]
      constraints = ["FoodTagAssoc.foodtag_id=FoodTag.id", "FoodTagAssoc.food_id=%d"%fid]
      tags = sorted([v["FoodTag.name"] for v in \
                     db_handler.get(["FoodTag", "FoodTagAssoc"], constraints=constraints)])
      data = {}
      for col in ["id", "name", "life", "image_url"]:
        return_key = "%s_%s"%(table.lower(), col)
        row_key = "%s.%s"%(table, col)
        data[return_key] = foods[0][row_key] if row_key in foods[0] else None
      data["food_tags"] = tags
      logging.info("%s data=%s", func_name, str(data))
      self.sendData(data)
    else:
      self.sendError(404, message='Food{id:%d} Not Found.'%fid, caller=func_name)

  def getInventory(self):
    func_name = inspect.stack()[0][3]
    db_handler = DatabaseHandler(AppHandler.db, AppHandler.user, AppHandler.passwd, AppHandler.host)
    item_reads = db_handler.getPresentItemReads(kitchen_id=self.uid)
    data = []
    now = datetime.datetime.utcnow()
    for ir in item_reads:
      r = {}
      for (key, value) in ir.items():
        r[key.lower().replace(".", "_")] = value
      predecessors = db_handler.get(["ItemRead", "Event"], 
                                    constraints=["ItemRead.item_id=%d"%ir["Item.id"],
                                                 "ItemRead.arrival_event_id=Event.id"],
                                    order_bys=["Event.time"])
      r["initial_weight"] = predecessors[0]["ItemRead.weight"]
      r["initial_time"] = predecessors[0]["Event.time"]
      r["age"] = (now - timeStringToDateTime(r["initial_time"])).total_seconds() / (60.0*60*24)
      r["life"] = ir["Food.life"]
      if ir["Food.life"] != None:
        r["remaining_time"] = ir["Food.life"] - r["age"]
        r["fraction_life"] = r["age"] / ir["Food.life"]
        r["fraction_remaining"] = r["remaining_time"] / ir["Food.life"]
      else:
        r["remaining_time"], r["fraction_life"] = None, None
        logging.info("remaining_time --> %s %s %s", str(r["remaining_time"]), str(r["fraction_life"]), str(ir["Food.name"]))
      data.append(r)
    logging.info("%s sending inventory data=%s...", func_name, str(data)[:100])
    self.sendData(data)
 
  def processGetRecipes(self, pathparts):
    func_name = inspect.stack()[0][3]
    d = self._extractDict(pathparts, 
                          ["all_ingredients", "include_ingredients", "exclude_ingredients",
                           "keywords", "page", "per_page", "sortby"],
                          "Recipes", func_name)
    if d == None: return
    all_ingredients = d["all_ingredients"]
    include_ingredients = d["include_ingredients"]
    exclude_ingredients = d["exclude_ingredients"]
    keywords, sortby = d["keywords"], d["sortby"]
    per_page, page = d["per_page"], d["page"]
    self.getRecipes(all_ingredients, include_ingredients, exclude_ingredients,
                    keywords, sortby, per_page, page)
    
  def getRecipes(self, all_ingredients, include_ingredients, exclude_ingredients,
                 keywords, sortby, per_page, page):
    """Get sorted recipes given ingredients and keywords."""
    func_name = inspect.stack()[0][3]
    unknown_sortby = set(sortby).difference(set(AppHandler.recipe_handler.sortby_methods))
    if unknown_sortby:
      args = str(sortby), str(AppHandler.recipe_handler.sortby_methods)
      self.sendError(400, "Recipe sortby method(s) %s not in %s" % args)
      return
    data = AppHandler.recipe_handler.getRecipes(keywords=keywords,
                                                all_ingredients=all_ingredients,
                                                include_ingredients=include_ingredients,
                                                exclude_ingredients=exclude_ingredients,
                                                sortby=sortby, per_page=per_page, page=page)
    logging.info("%s sending recipe data=%s...", func_name, str(data)[:100])
    self.sendData(data)

  def processGetSplit(self, pathparts):
    func_name = inspect.stack()[0][3]
    d = self._extractDict(pathparts, ["previousSplits"], "Split", func_name)
    if d == None: return
    self.getSplit(d["previousSplits"])
  
  def getSplit(self, previous_splits):
    """ Get split."""
    func_name = inspect.stack()[0][3]
    logging.info("%s before split()", func_name)
    data = AppHandler.recipe_handler.split(previous_splits)
    logging.info("%s sending split data=%s.", func_name, str(data))
    self.sendData(data)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--data", help="Data.", default=DATA)
    parser.add_argument("--log", help="Log file.")
    parser.add_argument("--service-config", help="Service config.", default=API_CONFIG)
    parser.add_argument("--init-handler", help="Initialize hash.", action='store_true')
    args = parser.parse_args()
    
    if not args.log: args.log = default=join(args.data, "app.log")
    configureLogging(args.log)
    config = json.loads(open(args.service_config).read())
    
    ble_url = config["base-url"] + str(config["ble-api-port"])
    s = AppServerWrapper(config["host"], config["app-api-port"], config["db"], \
                         config["db-user"], config["db-passwd"], config["db-host"],
                         ble_url, args.init_handler)
    s.serveSync()
    #s.listenForSignal()
    #s.shutdown()
    
