import collections

import mclinterface
import common

def convert_query_response_to_dict( query_response ):
    result = MarkovModel() 

    if not query_response.has_key('rows'):
        print "no rows for jobId:", query_response['jobReference']['jobId'] 
        return result

    for row in query_response['rows']:
        fields = row['f'];
        first = fields[0]['v'];
        second = fields[1]['v'];
        hits = fields[2]['v'];
        result[first][second]["hits"] = int(hits)
    return result;

def compute_node_degrees(model, clusters):
    degrees = GraphDegree() 

    for k,v in model.iteritems():
        for k2,v2 in model[k].iteritems():
            degrees[k]["out"].add(k2)
            degrees[k2]["in"].add(k)

    result = {}
    for k,v in degrees.iteritems():
        result[k] = {
                "indegree": len(v["in"]), 
                "outdegree": len(v["out"]),
                "cluster": get_cluster(k, clusters) }

    return result 

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

def aggregate_query_responses( query_responses ):
    aggregated = MarkovModel()
    for index, query_response in enumerate(query_responses):
        print " aggregate %i of %i..." % (index+1, len(query_responses))
        d = convert_query_response_to_dict( query_response )
        for k1,v1 in d.iteritems():
            for k2,v2 in v1.iteritems():
                aggregated[k1][k2]['hits'] += v2['hits']

    for k1,v1 in aggregated.iteritems():
        total = 0
        for k2,v2 in v1.iteritems():
            total += v2['hits']
        for k2,v2 in v1.iteritems():
            v2['weight'] = v2['hits'] / float(total)

    return aggregated

def munge(query_responses):
    model = aggregate_query_responses(query_responses)
    clusters = mclinterface.get_clusters(model)
    node_degrees = compute_node_degrees(model, clusters)
    cluster_model = build_cluster_model(model, clusters)
    cluster_degrees = compute_cluster_degrees(model, clusters)

    results = {
        'event_cluster_model' : cluster_model,
        'event_model' : model, 
        'node_degrees' : node_degrees,
        'cluster_degrees' : cluster_degrees,
    }

    print "processing complete."
    return results
