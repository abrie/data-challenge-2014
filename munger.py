import collections
import numpy
import time

import mclinterface
import common

def trim_type_name(type_name):
    trimmed = type_name.replace("Event","")
    print type_name, trimmed
    return trimmed

def convert_query_response_to_eventtimes( query_response ):
    result = EventTimes()

    for row in query_response['rows']:
        fields = row['f']
        event = trim_type_name(fields[0]['v'])
        first = long(fields[1]['v'])
        last = long(fields[2]['v'])

        result[event]["first"] = first 
        result[event]["last"] = last 

    return result

def convert_query_response_to_markovmodel( query_response ):
    result = MarkovModel() 

    for row in query_response['rows']:
        fields = row['f']
        first = trim_type_name(fields[0]['v'])
        second = trim_type_name(fields[1]['v'])
        hits = int(fields[2]['v'])

        result[first][second]["hits"] = hits

    for k1,v1 in result.iteritems():
        total = 0
        for k2,v2 in v1.iteritems():
            total += v2['hits']
        for k2,v2 in v1.iteritems():
            v2['weight'] = v2['hits'] / float(total)

    return result;

def convert_query_response_to_markovstate( query_response ):
    result = MarkovState() 

    for row in query_response['rows']:
        fields = row['f'];
        state = trim_type_name(fields[0]['v']);
        hits = int(fields[1]['v']);
        result[state]["hits"] = hits
    return result;

def compute_node_degrees(model, clusters):
    degrees = GraphDegree() 

    for k,v in model.iteritems():
        cluster_a = get_cluster(k, clusters)
        for k2,v2 in model[k].iteritems():
            cluster_b = get_cluster(k2, clusters)
            if cluster_a == cluster_b:
                degrees[k]["out"].add(k2)
                degrees[k2]["in"].add(k)

    result = {}
    for k,v in degrees.iteritems():
        result[k] = { "indegree": len(v["in"]), "outdegree": len(v["out"]) }

    return result 

def EventTimes():
    return collections.defaultdict(
            lambda: {"first":0,"last":0})

def MarkovState():
    return collections.defaultdict(
            lambda: {"hits":0})

def MarkovModel():
    return collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: {"hits":0, "weight":0})) 
    
def GraphDegree():
    return collections.defaultdict(
            lambda: {"in":set(), "out":set()}) 

def get_cluster(event, event_cluster_map):
    return event_cluster_map[event]

def build_cluster_model(event_model, event_clusters):
    model = MarkovModel()
    totals = collections.defaultdict(lambda:0)

    for k,v in event_model.iteritems():
        cluster_a = get_cluster(k, event_clusters)
        for k2,v2 in v.iteritems():
            cluster_b = get_cluster(k2, event_clusters)
            model[cluster_a][cluster_b]["hits"] += 1
            totals[cluster_a] += 1
        for k2,v2 in v.iteritems():
            total = totals[cluster_a]
            cluster_b = get_cluster(k2, event_clusters)
            weight = model[cluster_a][cluster_b]["hits"] / float(total)
            model[cluster_a][cluster_b]["weight"] = weight 

    return model

def compute_cluster_degrees(event_model, event_clusters):
    nodes = GraphDegree() 

    for k,v in event_model.iteritems():
        cluster_a = get_cluster(k, event_clusters)
        for k2,v2 in v.iteritems():
            cluster_b = get_cluster(k2, event_clusters)
            nodes[cluster_a]["out"].add( cluster_b  )
            nodes[cluster_b]["in"].add( cluster_a )

    return { 
            cluster_id: { 
                "indegree": len(events["in"]),
                "outdegree": len(events["out"])
            } for cluster_id, events in nodes.iteritems()
        }

def munge_times(query_responses):
    result = convert_query_response_to_eventtimes(query_responses[0])
    print "lifetimes measured."
    return result

def munge_state(query_responses):
    result = convert_query_response_to_markovstate(query_responses[0])
    print "population counted."
    return result
    
def compute_stationary_model(model):
    row_names = set() 
    col_names = set()
    for k,v in model.iteritems():
        row_names.add(k)
        for k2,v2 in v.iteritems():
            col_names.add(k)

    row_names = sorted(row_names)
    col_names = sorted(col_names)

    rows_cols = [];
    for row_name in row_names:
        row = []
        for col_name in col_names:
            row.append(model[row_name][col_name]["weight"])
        rows_cols.append(row)

    # based on: http://stackoverflow.com/q/10504158
    matrix = numpy.array(rows_cols)
    for i in xrange(10):
        matrix = numpy.dot(matrix, matrix)

    print "equilibrium probabilities:"
    print matrix[0]

    result = {}
    for name, value in zip(row_names, matrix[0].tolist()):
        result[name] = value

    return result

def munge_model(query_responses):
    model = convert_query_response_to_markovmodel(query_responses[0])
    clusters = mclinterface.get_clusters(model)
    node_degrees = compute_node_degrees(model, clusters)
    cluster_model = build_cluster_model(model, clusters)
    cluster_degrees = compute_cluster_degrees(model, clusters)
    stationary_model = compute_stationary_model(model)

    results = {
        'stationary_model' : stationary_model,
        'cluster_model' : cluster_model,
        'event_model' : model, 
        'node_degrees' : node_degrees,
        'clusters' : clusters,
        'cluster_degrees' : cluster_degrees,
    }

    print "model constructed."
    return results
