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
import collections, gurobipy, time, numpy as np

sq = lambda x: x*x

def clearWeightData(item_reads, max_range=None):
    """Clears ItemRead weight data.
    
    Clears weight data for all uncertain ItemRead dicts.
    
    Args:
        item_reads: List of ItemRead dicts.
        max_range: Maximum max-min range for which we will not clear.
    
    Returns:
        List of updated ItemRead dicts.
    """
    item_reads = [v.copy() for v in item_reads]
    strs = "ItemRead.weight", "ItemRead.min_weight", "ItemRead.max_weight"
    for ir in item_reads:
        if max_range==None or ir[strs[-1]]-ir[strs[1]] > max_range:
            for s in strs:
                ir[s] = None
    return item_reads

def variablesToValues(data, to_type=float):
    """Converts Gurobi variables to built-in type or specified type.
    
    Converts Gurobi variables to built-in type or specified type.
        If the the variable is a mapping or iterable, converts recursively.
    
    Args:
        data: Data to convert.
        to_type: Data type to convert to.
    
    Returns:
        Converted data or data structure.
    """
    if type(data) == gurobipy.Var: data = data.x
    if isinstance(data, collections.Mapping):
        return dict([variablesToValues(v, to_type) for v in data.iteritems()])
    elif isinstance(data, collections.Iterable):
        return type(data)([variablesToValues(v, to_type) for v in data])
    elif to_type==int:
        return int(round(data)) 
    elif type(data) in [int, float]:
        return data
    elif type(data) in [np.float64]:
        return float(data)
    else:
        raise("Cannot convert from variable to value.")

# ------- Item Read Weight Optimization -------
def itemReadPredicted(W, A, R, t):
    """Weight predicted at time t.
    
    Weight predicted by given weight vector W at time t given
        arrival and removal matrices A and R.

    Args:
        W: R^N weight vector where N is the number of ItemReads.
        A: R^{TxN} arrival matrix where A[t][i] is whether 
            ItemRead i arrived at time t.
        R: R^{TxN} removal matrix where R[t][i] is whether 
            ItemRead i was removed at time t.
        t: time.
    
    Returns:
        Predicted weight.
    """
    return sum([w*(a-r) for (w, a, r) in zip(W, A[t], R[t]) if a-r and w!=None])

def itemReadLoss(W, A, R, S):
    """Scale loss (aka sq(actual_weight-predicted_weight)).
    
    Total loss over all time for the given scale.

    Args:
        W: R^N weight vector where N is the number of ItemReads.
        A: R^{TxN} arrival matrix where A[t][i] is whether 
            ItemRead i arrived at time t.
        R: R^{TxN} removal matrix where R[t][i] is whether 
            ItemRead i was removed at time t.
        S: R^T scale weight vector.
    
    Returns:
        Total loss
    """
    return sum([sq(S[t] - itemReadPredicted(W, A, R, t)) \
                for t in range(len(S)) if S[t]!=None])

def optimizeItemReadWeights(events, item_reads):
    """Compute weights for ItemReads given Events.
    
    Args:
        events: List of Event dicts.
        item_reads: List of ItemRead dicts.
    
    Returns:
        List of updated ItemRead dicts.
    """
    obj, item_reads = 0.0, [v.copy() for v in item_reads]
    # optimize surfaces separately
    for surface in set([v["Event.surface"] for v in events if v["Event.surface"]]):
        _, surface_item_reads, W, A, R, S \
            = getItemReadVariables(events, item_reads, surface)
        m = gurobipy.Model()
        m.setParam("OutputFlag", False)
        W = [m.addVar() if w==None else w for w in W]
        m.update()
        m.setObjective(itemReadLoss(W, A, R, S), gurobipy.GRB.MINIMIZE)
        m.optimize()
        W = variablesToValues(W)
        for (item, w) in zip(surface_item_reads, W):
            item["ItemRead.weight"] = w
        obj += m.objVal
    return obj, item_reads

def optimizeItemReadWeightBounds(events, item_reads):
    """Compute min_weights and max_weights for ItemReads given Events.
    
    Args:
        events: List of Event dicts.
        item_reads: List of ItemRead dicts.
    
    Returns:
        List of updated ItemRead dicts.
    """
    item_reads = [v.copy() for v in item_reads]
    # optimize surfaces separately
    for surface in set([v["Event.surface"] for v in events if v["Event.surface"]]):
        _, surface_item_reads, W, A, R, S \
            = getItemReadVariables(events, item_reads, surface)
        # Get the optimal weights and losses.
        W_opt = [v for v in W]
        l_opt = [abs(S[t]-itemReadPredicted(W_opt, A, R, t)) if S[t]!=None else None \
                 for t in range(len(S))]
        # For each item, find the minimum and maximum weights that still achieve
        # (near) optimal objectives.
        for (i, item_read) in enumerate(surface_item_reads):
            for (mstr, opt_dir) in zip(["ItemRead.min_weight","ItemRead.max_weight"],
                                       [gurobipy.GRB.MINIMIZE, gurobipy.GRB.MAXIMIZE]):
                if item_read[mstr]: continue
                m = gurobipy.Model()
                m.setParam("OutputFlag", False)
                W = [m.addVar() for v in W]
                m.update()
                m.setObjective(W[i], opt_dir)
                m.addConstr(W[i] <= 1e4) # So not unbounded
                for t in range(len(S)):
                    if S[t] == None: continue
                    l = S[t]-itemReadPredicted(W, A, R, t)
                    if type(l)==gurobipy.LinExpr:
                        m.addConstr(-l_opt[t]-1.0 <= l), m.addConstr(l <= l_opt[t]+1.0)
                m.optimize()
                item_read[mstr] = m.objVal
    return item_reads

def getItemReadVariables(events, item_reads, surface):
    """Get ItemRead values.
    
    Return all variables used in ItemRead optimizations.

    Args:
        events: List of Event dicts.
        item_reads: List of ItemRead dicts.
        surface: Surface for which to return variables.
    
    Returns:
        Tuple of variables consisting of the following:
            surface_events: Same as events but only for this surface.
            surface_item_reads: Same as item_reads but only for this surface.
            W: R^N weight vector where N is the number of surface ItemReads.
            A: R^{TxN} arrival matrix where A[t][i] is whether ItemRead i 
                arrived at time t.
            R: R^{TxN} removal matrix where R[t][i] is whether ItemRead i
                was removed at time t.
            S: R^T scale weight vector.
    """
    # Get all events for this surface and for events 
    # not associated with any surface (no weight data).
    surface_events = [v for v in events if v["Event.surface"]==surface or v["Event.surface"]==None]
    # Get all item reads that arrived at and/or were removed from this surface.
    surface_item_reads = [v for v in item_reads if v["ArrivalEvent.surface"]==surface or \
                          ("RemovalEvent.surface" in v and v["RemovalEvent.surface"]==surface)]
    T, N = len(surface_events), len(surface_item_reads)
    times, S = zip(*sorted([(str(v["Event.time"]), v["Event.event_force"]) for v in surface_events]))
    # Arrival and removal matrices
    A, R = [[[0 for i in range(N)] for t in range(T)] for v in range(2)]
    for (i, item) in enumerate(surface_item_reads):
        t_arrival = times.index(item["ArrivalEvent.time"])
        A[t_arrival][i] = 1
        if "RemovalEvent.time" in item:
            t_removal = times.index(item["RemovalEvent.time"])
            R[t_removal][i] = 1
    # Get optimization variables.
    W = [v["ItemRead.weight"] for v in surface_item_reads]
    return surface_events, surface_item_reads, W, A, R, S

# ------- Basket Weight Optimization -------
def deltaPredicted(deltas, t):
    return sum([deltas[i][t] for i in range(t+1)])

def basketLoss(W, R, Q, S, C, alpha=0.5, beta=0.5, gamma=0.5, output_flag=False):
    T = len(S)
    deltas = [[W[i][t]-(W[i][t-1] if t else 0.0) for t in range(T)] for i in range(T)]
    sum_sq_term = sum([sq(S[t] - deltaPredicted(deltas, t)) for t in range(T)])
    cost_term = sum([C[i][t]*deltas[i][t] for i in range(T) for t in range(i+1,T) \
                     if deltas[i][t] and C[i][t]])
    if output_flag:
        for t in range(T):
            print "time", t
            print "\tObject deltas", [int(deltas[v][t]) for v in range(T)]
            print "\tScale changes", int(S[t])
            print "\tPredi changes", int(deltaPredicted(deltas, t))
    return alpha*sum_sq_term + (1-alpha)*cost_term + beta*np.sum(R) + gamma*np.sum(Q)

def optimizeBasketWeights(events, C, alpha=1e0, beta=1e3, gamma=1e0, output_flag=False, **kwargs):
    W_max, obj, baskets = 5e3, 0.0, []
    times = [v["time"] for v in events]
    for surface in set([v["surface"] for v in events]):
        surface_events, S, C_s = getBasketVariables(events, C, surface)
        surface_times = [v["time"] for v in surface_events]
        m = gurobipy.Model()
        m.setParam("OutputFlag", output_flag)
        T = len(S)
        W = [[m.addVar() if t>=i else 0 for t in range(T)] for i in range(T)]
        R = [[m.addVar(vtype=gurobipy.GRB.BINARY) if t>i else 0 for t in range(T)] for i in range(T)]
        Q = [[m.addVar(vtype=gurobipy.GRB.BINARY) if t>=i else 0 for t in range(T)] for i in range(T)]
        m.update()
        [m.addConstr(W[i][t]<=W[i][t-1]) for i in range(T) for t in range(i+1,T)]
        [m.addConstr((W[i][t-1]-W[i][t])/W_max<=R[i][t]) for i in range(T) for t in range(i+1,T)]
        [m.addConstr(W[i][t]/W_max<=Q[i][t]) for i in range(T) for t in range(i,T)]
        m.update()
        m.setObjective(basketLoss(W, R, Q, S, C_s, alpha=alpha, beta=beta, gamma=gamma),
                       gurobipy.GRB.MINIMIZE)
        m.update()
        #m.params.timelimit = 20.0
        m.optimize()
        W, R, Q = map(variablesToValues, [W, R, Q])
        for w in W:
            basket, bw = [None if v not in surface_times else w[surface_times.index(v)] for v in times], 0
            for i in range(len(basket)):
                if basket[i] != None: bw = basket[i]
                else: basket[i] = bw
            baskets.append(basket)
        if output_flag:
            print surface
            print "\tS =", map(int, S)
            print "\tRemovals, Non-empty = %d, %d" % (np.sum(R), np.sum(Q))
            print "\t"+"\n\t".join(map(str, [map(int,w) for w in W]))
            basketLoss(W, R, Q, S, C_s, alpha=alpha, beta=beta, gamma=gamma, output_flag=True)
        obj += m.objVal
    return obj, baskets

def makeItem(arrival_event, removal_event):
    item = {}
    for (prefix, event) in zip(["arrivalevent_", "removalevent_"], [arrival_event, removal_event]):
        if event==None: event = dict([(v, None) for v in arrival_event.keys()])
        for (key, value) in event.items():
            item[prefix+key] = value
    return item

def basketsToItems(baskets, events):
    items = []
    for basket in baskets:
        assert(len(basket)==len(events))
        if not sum(basket): continue
        arrival = np.nonzero(basket)[0][0]
        for i in range(arrival, len(events)):
            if i==len(basket)-1 or basket[i] != basket[i+1]:
                item = makeItem(events[arrival], events[i+1] if i<len(basket)-1 else None)
                items.append(item)
                arrival = i+1
    return items
    
def getBasketVariables(events, C, surface):
    events = zip(*sorted([(v["time"], v) for v in events]))[1]
    inds, surface_events = zip(*[(i,v) for (i,v) in enumerate(events) if v["surface"]==surface])
    S = [v["event_force"] for v in surface_events]
    C_s = [[C[i][j] for j in inds] for i in inds]
    return surface_events, S, C_s

