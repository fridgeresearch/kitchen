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

Functions to perform database-related operations
"""
import sys, os, MySQLdb as mdb, networkx as nx
from os.path import *
sys.path.append(dirname(dirname(abspath(__file__))))
from kitchen import *
from utils.general_utils import *

def dbConnect(dict_cursor=True):
    """Connect to the Kitchen database.
    
    Args:
        dict_cursor: whether or not to use mdb.cursors.DictCursor.
    """    
    con = mdb.connect(user, passwd, db)
    cursor = con.cursor(mdb.cursors.DictCursor) if dict_cursor else con.cursor()
    return con, cursor

def getEventTime(cursor, event_id=None, event_time=None, order="DESC"):
    """Get the event time.

    If the event_time is specified, simply return.  Else if the event_id is
    specified, return its time. Else return the most recent event.
    
    Args:
        cursor: Database cursor.
        event_id: Event id.
        event_time: Event time.
        order: ASC or DESC.
    

    Returns:
        The event time string.
    """    
    if event_id == None:
        cursor.execute("SELECT id FROM Event ORDER BY time %s"%order)
        event_id = int(cursor.fetchone()["id"])
    if event_time == None:
        cursor.execute("SELECT time FROM Event WHERE id=%d"%event_id)
        event_time = str(cursor.fetchone()["time"])
    return event_time

def getEvents(cursor, start_event_id=None, start_event_time=None,
              end_event_id=None, end_event_time=None, kitchen_id=None):
    """Get the events between specified IDs or times.
    
    Args:
        cursor: Database cursor.
        start_event_id: Starting event id.
        start_event_time: Starting event time.
        end_event_id: Ending event id.
        end_event_time: Ending event time.
        kitchen_id: Kitchen ID.
    
    Returns:
        List of events in the specified range.
    """    
    # Get events between the specified times.
    start_event_time = getEventTime(cursor, start_event_id, start_event_time, order="ASC")
    end_event_time = getEventTime(cursor, end_event_id, end_event_time, order="DESC")
    kitchen_id_cond = ("AND kitchen_id=%d"%kitchen_id) if kitchen_id!=None else ""
    qry = 'SELECT * FROM Event WHERE time>="%s" AND time<="%s" %s ORDER BY time'
    cursor.execute(qry % (start_event_time, end_event_time, kitchen_id_cond))
    return convertToStrings(map(dict,list(cursor.fetchall())))

def getItemReads(cursor, start_event_id=None, start_event_time=None, 
                 end_event_id=None, end_event_time=None, kitchen_id=None,
                 table_cols={"ItemRead":["id", "min_weight", "max_weight", "weight"], 
                             "Item":["id", "kitchen_id"], 
                             "ArrivalEvent":["id", "time", "surface", "event_force", "x", "y", "z"],
                             "RemovalEvent":["id", "time", "surface", "event_force", "x", "y", "z"],
                             "Food":["id", "name"]}):
    """Get all items in the specified range.
    
    Get all items in the specified range. Return list of dictionaries with the 
    specified columns from the specified tables.
    
    Args:
        cursor: Database cursor.
        start_event_id: Starting event id.
        start_event_time: Starting event time.
        end_event_id: Ending event id.
        end_event_time: Ending event time.
        kitchen_id: Kitchen ID.
        table_cols: Dict where keys are table names and values are lists of
            column names.
    
    Returns:
        List of items in the specified range.
    """    
    # Get the all items that were added before (or during) the event.
    start_event_time = getEventTime(cursor, start_event_id, start_event_time, order="ASC")
    end_event_time = getEventTime(cursor, end_event_id, end_event_time, order="DESC")
    kitchen_id_cond = (" AND Item.kitchen_id=%d "%kitchen_id) if kitchen_id!=None else ""
    base = [("Event","ArrivalEvent"), ("Food","Food"), ("Item","Item"), ("ItemRead","ItemRead")]
    extra = [("Event", "RemovalEvent")]
    conds = '''WHERE Item.food_id=Food.id
                 AND ItemRead.item_id=Item.id
                 AND ItemRead.arrival_event_id=ArrivalEvent.id
                 AND ArrivalEvent.time<="%s"''' + kitchen_id_cond
    qry = prepareSelect(cursor, base + extra, [], table_cols) + conds + \
          '''    AND ItemRead.removal_event_id=RemovalEvent.id
                 AND RemovalEvent.time>="%s"'''
    cursor.execute(qry % (end_event_time, start_event_time))
    eventually_removed = list(cursor.fetchall())
    # TODO: shared functionality with optimization
    eventually_removed = map(dict, eventually_removed)
    for item in eventually_removed:
        if item["removalevent_time"] > end_event_time:
            for s in [v for v in item.keys() if "removalevent_" in v]: item[s] = None
    # end TODO
    qry = prepareSelect(cursor, base, extra, table_cols) + conds + "AND ItemRead.removal_event_id IS NULL"
    cursor.execute(qry % end_event_time)
    never_removed = list(cursor.fetchall())
    items = convertToStrings(map(dict, eventually_removed + never_removed))
    items = sorted(items, key=lambda x: x["arrivalevent_time"])
    return items

def prepareSelect(cursor, tbls, null_tbls, table_cols):
    s = []
    for (tbl, tbl_alias) in tbls:
        for col in table_cols[tbl_alias] if tbl_alias in table_cols else []:
            s.append("%s.%s as %s_%s"%(tbl_alias, col, tbl_alias.lower(), col.lower()))
    for (tbl, tbl_alias) in null_tbls:
        for col in table_cols[tbl_alias] if tbl_alias in table_cols else []:
            s.append("NULL as %s_%s"%(tbl_alias.lower(), col.lower()))
    select_statement = "SELECT " + (', '.join(s)) + "\n"
    from_statement = "FROM " + (', '.join("%s as %s"%v[:2] for v in tbls)) + "\n"
    return select_statement + from_statement
    
def getFoodNames(cursor):
    """Get dictionary from food id to food name."""
    cursor.execute("SELECT id, name FROM Food")
    return dict([v.values() for v in cursor.fetchall()])

def getEventAddedItems(cursor, event_id):
    """Get list of food ids of items added at the specified event."""
    cursor.execute('SELECT food_id FROM Item WHERE arrival_event_id=%d;'%event_id)
    return [v[0] for v in cursor.fetchall()]

def getEventRemovedItems(cursor, event_id):
    """Get list of food ids of items removed at the specified event."""
    cursor.execute('SELECT food_id FROM Item WHERE removal_event_id=%d;'%event_id)
    return [v[0] for v in cursor.fetchall()]

def getEventItems(cursor, event_id):
    """Get list of food ids of items added or removed at the specified event."""
    return getEventAddedItems(cursor, event_id) + getEventRemovedItems(cursor, event_id)

def deleteSubtree(G, fid):
    """Delete subtree at the specified food id."""
    [G.remove_node(v) for v in nx.dfs_tree(G, fid)]

def getFoodGraph(cursor):
    """get the food graph."""
    G = nx.DiGraph()
    cursor.execute("SELECT parent_food_id, child_food_id FROM FoodRelation")
    G.add_edges_from([v.values() for v in cursor.fetchall()])
    return G

def getFoodAncestors(cursor, graph):
    """Get ancestors for the 'Food' class."""
    cursor.execute("SELECT id FROM Food WHERE name='Food'")
    src = cursor.fetchone()["id"]
    return nx.single_source_shortest_path(graph, src)
