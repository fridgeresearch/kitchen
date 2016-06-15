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

Database handler.
"""
import sys, os, warnings, MySQLdb as mdb

class DatabaseHandler:
    def __init__(self, db, user, passwd, host, warnings=True, create=False):
        """Initialize."""
        if not warnings:
            warnings.filterwarnings('ignore', category = mdb.Warning)
        if create:
            create_con = mdb.connect(user=user, passwd=passwd, host=host)
            create_cursor = create_con.cursor()
            create_cursor.execute('CREATE DATABASE %s' % db)
            create_cursor.close()
        self.db_name = db
        self.con = mdb.connect(db=db, user=user, passwd=passwd, host=host)
        self.cursor = self.con.cursor(mdb.cursors.DictCursor)
        self._initTableCols()        
    def _initTableCols(self):
        """Initialize internal table cols data structure."""
        cursor = self.con.cursor()
        self.table_cols = {}
        cursor.execute("SHOW TABLES")
        for (table,) in cursor:
            cursor.execute("SELECT * FROM "+table)
            self.table_cols[table] = [v[0] for v in cursor.description]
        cursor.close()
    def printDb(self):
        for (table, cols) in sorted(self.table_cols.items()):
            rows = self.get([table])
            #if table!="GroceryList": continue
            print table
            rows = [[r["%s.%s"%(table,c)] for c in cols] for r in rows]
            rows_t = [[] for var in range(len(cols))]
            for v in rows + [cols]:
                for (i, x) in enumerate(v):
                    rows_t[i].append(x)
            widths = [max(map(len, map(str, v)))+2 for v in rows_t]
            max_len = 100
            print '|  '.join([str(v).ljust(min(widths[i], max_len)) for (i, v) in enumerate(cols)])
            for row in rows:
                print '|  '.join([str(v)[:max_len].ljust(widths[i]) for (i, v) in enumerate(row)])
            print
    def checkAuth(self, user, passwd):
        constraints = ["name LIKE '%s'"%user, "pwd LIKE password('%s')"%passwd]
        r = self.get(["Kitchen"], constraints=constraints)
        if not r:
            return None
        else:
            return r[0]
    def dropDatabase(self):
        self.cursor.execute('DROP DATABASE IF EXISTS %s' % self.db_name)
        self.table_cols = {}
    def createDatabase(self):
        self.cursor.execute('CREATE DATABASE %s' % self.db_name)
        self.cursor.execute('USE %s' % self.db_name)
        self._initTableCols()
    def tableExists(self, table):
        qry = '''SELECT * FROM information_schema.tables
                  WHERE table_name="%s"
                    AND table_schema="%s"'''
        self.cursor.execute(qry % (table, self.db_name))
        return self.cursor.fetchone() != None
    def dropTable(self, table):
        self.cursor.execute("DROP TABLE IF EXISTS %s" % table)
        self._initTableCols()
    def createTable(self, table, cols, col_props):
        cs = ', '.join(["%s %s"%v for v in zip(cols, col_props)])
        self.cursor.execute("CREATE TABLE %s (%s)" % (table, cs))
        self._initTableCols()
    def insert(self, table, obj):
        self.insertMany(table, [obj])
    def insertMany(self, table, objs):
        if not objs:
            return
        else:
            # Convert any passwords.
            for obj in objs:
                for (k, v) in obj.items():
                    if isinstance(v, basestring) and not v.find("password("):
                        self.cursor.execute("SELECT %s"%v)
                        obj[k] = self.cursor.fetchone()[v]
            # Now insert.
            row_cols = [tuple(sorted(v.keys())) for v in objs]
            if len(set(row_cols)) != 1:
                raise Exception("Column names must match for insertion.")
            cols = row_cols[0]
            cols_str = ', '.join(cols)
            vals = ', '.join(["%s"]*len(cols))
            qry = 'INSERT INTO %s (%s) VALUES (%s)' % (table, cols_str, vals)
            to_insert = [tuple([v[w] for w in cols]) for v in objs]
            self.cursor.executemany(qry, to_insert)
    def update(self, table, obj, constraints=[]):
        insert_obj = {}
        for (k, v) in obj.items():
            if v==None:
                insert_obj[k] = "NULL"
            elif isinstance(v, basestring) and v.find("password("):
                insert_obj[k] = "'%s'"%v
            else:
                insert_obj[k] = str(v)
        vals = ', '.join(['%s=%s'%(k, v) for (k, v) in insert_obj.items()])
        where_clause = " AND ".join(constraints) if constraints else ""
        qry = 'UPDATE %s SET %s WHERE %s' % (table, vals, where_clause)
        self.cursor.execute(qry)
    def delete(self, table, constraints=[]):
        where_clause = " AND ".join(constraints) if constraints else ""
        qry = 'DELETE FROM %s ' % table
        if constraints:
            qry = qry + ('WHERE %s' % where_clause)
        self.cursor.execute(qry)
    def get(self, tables, table_aliases=[], cols=[], constraints=[], order_bys=[]):
        """Gets specified column tables from db given WHERE and ORDER BY clauses.
    
        Args:
            tables: Table(s) to get from.
            table_aliases: Aliases for tables or [] if table names
            cols: Column(s) specified (or [] if want all columns returned).
                Note that should be of the form Table.column.
            constraints: Constraints for where clause.
            order_bys: Columns to order by.
        
        Returns:
            Query result dictionary."""
        # Construct FROM clause
        if not table_aliases: table_aliases = tables
        if len(set(table_aliases)) != len(table_aliases):
            raise Exception("Must have unique table names.")
        from_clause = 'FROM %s' % ', '.join(["%s as %s"%v for v in zip(tables, table_aliases)])
        # Construct SELECT clause
        if not cols:
            cols = ["%s.%s"%(ta,c) for (t,ta) in zip(tables, table_aliases) \
                    for c in self.table_cols[t]]
        col_aliases = [v.lower().replace(".", "_") for v in cols]
        select_clause = 'SELECT %s' % ', '.join(["%s as %s"%v for v in zip(cols, col_aliases)])
        # Construct WHERE clause
        where_clause = ("WHERE %s" % (" AND ".join(constraints))) if constraints else ""
        # Construct ORDER BY clause
        order_by_clause = ("ORDER BY %s" % (", ".join(order_bys))) if order_bys else ""
        # Execute query and return dictionary result.
        qry = '%s %s %s %s' % (select_clause, from_clause, where_clause, order_by_clause)
        self.cursor.execute(qry)
        return [dict([(c,v[a]) for (c, a) in zip(cols, col_aliases)]) \
                for v in self.cursor.fetchall()]
    def getEvents(self, kitchen_id=None, segment_id=None,
                  start_time=None, end_time=None, cols=[], constraints=[]):
        """Get events
        
        Args:
            kitchen_id: Kitchen ID.
            segment_id: Segment ID.
            start_time: Time t where only return events with time >= t.
            end_time: Time t where only return events with time <= t.
        
        Returns:
            Event list."""
        constraints = [v for v in constraints]
        if kitchen_id != None:
            constraints.append('kitchen_id=%d'%kitchen_id)
        if segment_id != None:
            constraints.append('segment_id=%d'%segment_id)
        if start_time != None:
            constraints.append('time>="%s"'%start_time)
        if end_time != None:
            constraints.append('time<="%s"'%end_time)
        return self.get(["Event"], cols=cols, constraints=constraints,
                        order_bys=["time"])
    def getItemReads(self, kitchen_id=None, present_time=None,
                     omit_removed=False, omit_remaining=False):
        tables = ["Item", "ItemRead", "Food", "Event", "Event"]
        table_aliases = tables[:-2] + ["ArrivalEvent", "RemovalEvent"]
        constraints = ["Item.food_id=Food.id",
                       "ItemRead.item_id=Item.id",
                       "ItemRead.arrival_event_id=ArrivalEvent.id",
                       "ItemRead.removal_event_id=RemovalEvent.id"]
        if kitchen_id != None:
            constraints.append('Item.kitchen_id=%d'%kitchen_id)
        if present_time:
            constraints.append("ArrivalEvent.time<='%s'"%present_time)
            constraints.append("RemovalEvent.time>='%s'"%present_time) # TODO(andrej, jake): discuss
        irs = []
        # Removed ItemReads.
        if not omit_removed:
            irs += self.get(tables, table_aliases=table_aliases,
                            constraints=constraints, order_bys=["ArrivalEvent.time"])
        # Remaining ItemReads
        if not omit_remaining:
            constraints = [v for v in constraints if "Removal" not in v] + \
                          ["ItemRead.removal_event_id IS NULL"]
            irs += self.get(tables[:-1], table_aliases=table_aliases[:-1], 
                            constraints=constraints, order_bys=["ArrivalEvent.time"])
        # FoodTags
        food_tag_hash = self.getFoodTagHash()
        for (i, ir) in enumerate(irs):
            name = ir["Food.name"]
            irs[i]["FoodTags"] = food_tag_hash[name] if name in food_tag_hash else []
        # Beacons
        beacons = dict([(v["Beacon.id"], v) for v in self.get(["Beacon"])])
        for (i, ir) in enumerate(irs):
            bid = ir["Item.beacon_id"]
            if bid in beacons: 
                for (k, v) in beacons[bid].items():
                    irs[i][k] = v
        return irs
    def getFoodTagHash(self):
        tags = self.get(["Food", "FoodTag", "FoodTagAssoc"],
                        constraints=["FoodTagAssoc.food_id=Food.id", "FoodTagAssoc.foodtag_id=FoodTag.id"])
        food_tag_hash = {}
        for t in tags:
            if t["Food.name"] not in food_tag_hash:
                food_tag_hash[t["Food.name"]] = []
            food_tag_hash[t["Food.name"]].append(t)
        return food_tag_hash
    def getPresentItemReads(self, kitchen_id=None):
        return self.getItemReads(kitchen_id=kitchen_id, omit_removed=True)
    def lastRowId(self):
        return self.cursor.lastrowid
    def commit(self):
        self.con.commit()
