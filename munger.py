import httplib2
import pprint
import sys
import json
import subprocess
import collections

def write_query_response(event_model, filename):
    with open(filename, 'w') as mcl_file:
        for k,v in event_model.iteritems():
            for k2,v2 in event_model[k].iteritems():
                fields = (k,k2,v2['weight'])
                line = '%s\t%s\t%f\n' % fields
                mcl_file.write(line)

def convert_query_response_to_dict( query_response ):
    result = MarkovModel() 

    if not query_response.has_key('rows'):
        print "no rows for jobId:", query_response['jobReference']['jobId'] 
        return result

    for row in query_response['rows']:
        fields = row['f'];
        first = fields[0]['v'];
        second = fields[1]['v'];
        count = fields[2]['v'];
        result[first][second]["hits"] = int(count)
    return result;
        
def run_mcl(input_filename, output_filename):
    print "**** subprocess will call as follows:"
    call_parameters = [
            "mcl/bin/mcl", input_filename,
            "-I","5.0",
            "--abc",
            "-o", output_filename]
    pprint.pprint(call_parameters)

    print "**** calling..."

    try:
        subprocess.check_call(call_parameters)
    except subprocess.CalledProcessError as err:
        print 'Error while invoking MCL subprocess'
        pprint.pprint(err)
        sys.exit(1)

    print "**** subprocess completed ****"

def map_events_to_clusters(input_filename):
    result = {}
    with open('data/mcl_output', 'r') as mcl_output:
        for index, line in enumerate( mcl_output.readlines() ):
            fields = line.rstrip('\n').split('\t')
            cluster_id = "cluster_%i" % index
            for field in fields:
                result[field] = cluster_id 
    return result

def build_event_model(filename, event_clusters):
    degrees = GraphDegree() 
    model = MarkovModel()

    with open(filename, 'r') as mcl_file:
        for line in mcl_file.readlines():
            fields = line.rstrip('\n').split('\t')
            first = fields[0]
            second = fields[1]
            weight = float(fields[2])
            model[first][second]["weight"] = weight
            model[first][second]["hits"] += 1
            degrees[first]["out"].add(second)
            degrees[second]["in"].add(first)

        result = {}
        for k,v in degrees.iteritems():
            result[k] = {
                    "indegree": len(v["in"]), 
                    "outdegree": len(v["out"]),
                    "cluster": get_cluster(k, event_clusters)}

    return (model, result)

def MarkovModel():
    return collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: {"hits":0, "weight":0})) 
    
def GraphDegree():
    return collections.defaultdict(
            lambda: {"in":set(), "out":set()}) 

def get_cluster(event, event_cluster_map):
    return event_cluster_map[event]

def build_event_cluster_model(event_model, event_clusters):
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

def write_results(results, filename):
    with open(filename, 'w') as outfile:
        prettyJson = json.dumps(results, indent=4, sort_keys=True )
        outfile.write( prettyJson )

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
    aggregated_query_response = aggregate_query_responses( query_responses )
    write_query_response(aggregated_query_response, "data/mcl_input")
    run_mcl("data/mcl_input","data/mcl_output")
    event_clusters = map_events_to_clusters("data/mcl_output")
    event_model, node_degrees = build_event_model("data/mcl_input", event_clusters)
    event_cluster_model = build_event_cluster_model(event_model, event_clusters)
    cluster_degrees = compute_cluster_degrees(event_model, event_clusters)

    results = {
        'event_cluster_model' : event_cluster_model,
        'event_model' : event_model, 
        'node_degrees' : node_degrees,
        'cluster_degrees' : cluster_degrees,
    }

    print "processing complete."
    return results
