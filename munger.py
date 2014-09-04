import collections
import numpy
import time

import mclinterface
import common

def trim_type_name(type_name):
    trimmed = type_name.replace("Event", "")
    return trimmed

def convert_rows_to_markovmodel(rows):
    model = MarkovModel()

    for row in rows:
        fields = row['f']
        event_a = trim_type_name(fields[0]['v'])
        event_b = trim_type_name(fields[1]['v'])
        hits = int(fields[2]['v'])

        model[event_a][event_b]["hits"] = hits

    for transitions in model.itervalues():
        total = 0
        for transition in transitions.itervalues():
            total += transition['hits']
        for transition in transitions.itervalues():
            transition['weight'] = transition['hits'] / float(total)

    return model

def convert_rows_to_markovstate(rows):
    result = MarkovState()

    for row in rows:
        fields = row['f']
        event = trim_type_name(fields[0]['v'])
        hits = int(fields[1]['v'])
        result[event]["hits"] = hits
    return result

def compute_node_degrees(model, clusters):
    degrees = GraphDegree()

    for event_a, transitions in model.iteritems():
        cluster_a = get_cluster(event_a, clusters)
        for event_b, transition in transitions.iteritems():
            if transition["hits"] > 0:
                cluster_b = get_cluster(event_b, clusters)
                if cluster_a == cluster_b:
                    degrees[event_a]["out"].add(event_b)
                    degrees[event_b]["in"].add(event_a)

    result = {}
    for event, events in degrees.iteritems():
        result[event] = {"indegree": len(events["in"]),
                         "outdegree": len(events["out"])}
    return result

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
    totals = collections.defaultdict(lambda: 0)

    for event_a, transitions in event_model.iteritems():
        cluster_a = get_cluster(event_a, event_clusters)
        for event_b in transitions.iterkeys():
            cluster_b = get_cluster(event_b, event_clusters)
            model[cluster_a][cluster_b]["hits"] += 1
            totals[cluster_a] += 1
        for event_b in transitions.iterkeys():
            total = totals[cluster_a]
            cluster_b = get_cluster(event_b, event_clusters)
            weight = model[cluster_a][cluster_b]["hits"] / float(total)
            model[cluster_a][cluster_b]["weight"] = weight

    return model

def compute_cluster_degrees(event_model, event_clusters):
    degrees = GraphDegree()

    for event, transitions in event_model.iteritems():
        cluster_a = get_cluster(event, event_clusters)
        for event_b, transition in transitions.iteritems():
            if transition["hits"] > 0:
                cluster_b = get_cluster(event_b, event_clusters)
                degrees[cluster_a]["out"].add(cluster_b)
                degrees[cluster_b]["in"].add(cluster_a)

    result = {}
    for cluster, clusters in degrees.iteritems():
        result[cluster] = {"indegree": len(clusters["in"]),
                           "outdegree": len(clusters["out"])}
    return result

def munge_state(query):
    rows = aggregate_rows(query["reply"])
    result = convert_rows_to_markovstate(rows)
    print "population counted."
    return result
    
def model_to_matrix(model):
    events = set()

    for event_a, transitions in model.iteritems():
        events.add(event_a)
        for event_b in transitions.iterkeys():
            events.add(event_b)

    rows_cols = []
    labels = sorted(list(events))
    for i in labels:
        row = []
        for j in labels:
            row.append(model[i][j]["weight"])
        rows_cols.append(row)

    return (labels, numpy.array(rows_cols))

def compute_stationary_model(model):
    event_list, matrix = model_to_matrix(model)

    # based on: http://stackoverflow.com/q/10504158
    for i in xrange(10):
        matrix = numpy.dot(matrix, matrix)

    print "equilibrium probabilities:"
    print matrix[0]

    result = {}
    for event, ratio in zip(event_list, matrix[0].tolist()):
        result[event] = ratio

    return result

def aggregate_rows(replies):
    aggregate = []
    for reply in replies:
        aggregate.extend(reply['rows'])
    return aggregate

def munge_model(query):
    rows = aggregate_rows(query["reply"])
    model = convert_rows_to_markovmodel(rows)
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
