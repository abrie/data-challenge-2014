import collections

import mclinterface
import common

def convert_query_response_to_markovmodel( query_response ):
    result = MarkovModel() 

    for row in query_response['rows']:
        fields = row['f'];
        first = fields[0]['v'];
        second = fields[1]['v'];
        hits = fields[2]['v'];
        result[first][second]["hits"] = int(hits)

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
        state = fields[0]['v'];
        hits = fields[1]['v'];
        weight = fields[2]['v'];
        result[state]["hits"] = int(hits)
        result[state]["weight"] = float(weight)
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

def MarkovState():
    return collections.defaultdict(
            lambda: {"hits":0, "weight":0})

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

def munge_state(query_responses):
    result = convert_query_response_to_markovstate(query_responses[0])
    print "markov state generation complete."
    return result
    
def munge_model(query_responses):
    model = convert_query_response_to_markovmodel(query_responses[0])
    clusters = mclinterface.get_clusters(model)
    node_degrees = compute_node_degrees(model, clusters)
    cluster_model = build_cluster_model(model, clusters)
    cluster_degrees = compute_cluster_degrees(model, clusters)

    results = {
        'cluster_model' : cluster_model,
        'event_model' : model, 
        'node_degrees' : node_degrees,
        'clusters' : clusters,
        'cluster_degrees' : cluster_degrees,
    }

    print "markov model generation complete."
    return results
