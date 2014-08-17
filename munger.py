import httplib2
import pprint
import sys
import json
import subprocess
import collections

def write_query_response(query_response, filename):
    with open(filename, 'w') as mcl_file:
        for row in query_response['rows']:
            fields = row['f'];
            first = fields[0]['v'];
            second = fields[1]['v'];
            count = fields[2]['v'];
            ratio = fields[3]['v'];
            if( ratio >= 0.05 ):
                mcl_file.write('{0}\t{1}\t{2}\n'.format(first,second,ratio))

def run_mcl(input_filename, output_filename):
    try:
        subprocess.check_call(["mcl/bin/mcl",input_filename,"-I","5.0","--abc", "-o",output_filename])
    except subprocess.CalledProcessError as err:
        print 'CalledProcessError:', pprint.pprint(err)

def map_events_to_clusters(input_filename):
    result = {}
    with open('data/mcl_output', 'r') as mcl_output:
        for index, line in enumerate( mcl_output.readlines() ):
            fields = line.rstrip('\n').split('\t')
            cluster_id = "cluster_%i" % index
            for field in fields:
                result[field] = cluster_id 
    return result

def build_markov_chain(filename, markov_clusters):
    degrees = collections.defaultdict(
            lambda: {"in":set(), "out":set()}) 
    
    nodes = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: {"hits":0, "weight":0})) 

    def map_event_to_cluster(event):
        return markov_clusters[event]

    with open(filename, 'r') as mcl_file:
        for line in mcl_file.readlines():
            fields = line.rstrip('\n').split('\t')
            first = fields[0]
            second = fields[1]
            ratio = float(fields[2])
            nodes[first][second]["weight"] = ratio
            nodes[first][second]["hits"] += 1
            degrees[first]["out"].add(second)
            degrees[second]["in"].add(first)

        result = {}
        for k,v in degrees.iteritems():
            result[k] = {
                    "indegree": len(v["in"]), 
                    "outdegree": len(v["out"]),
                    "cluster": map_event_to_cluster(k)}

    return (nodes, result)

def build_markov_cluster_chain(markov_chain, markov_clusters):
    nodes = collections.defaultdict(
            lambda: collections.defaultdict(
                lambda: {"hits":0, "weight":0})) 
    totals = collections.defaultdict(lambda:0)

    def map_event_to_cluster(event):
        return markov_clusters[event]

    for k,v in markov_chain.iteritems():
        cluster_a = map_event_to_cluster(k)
        for k2,v2 in v.iteritems():
            cluster_b = map_event_to_cluster(k2)
            nodes[cluster_a][cluster_b]["hits"] += 1
            totals[cluster_a] += 1
        for k2,v2 in v.iteritems():
            total = totals[cluster_a]
            cluster_b = map_event_to_cluster(k2)
            weight = nodes[cluster_a][cluster_b]["hits"] / float(total)
            nodes[cluster_a][cluster_b]["weight"] = weight 

    return nodes

def write_results(results, filename):
    with open(filename, 'w') as outfile:
        prettyJson = json.dumps(results, indent=4, sort_keys=True )
        outfile.write( prettyJson )

#experimental method, probably deprecated.
def write_cluster_to_mcl_input(markov_chains, markov_clusters, cluster_id, filename):
    def map_event_to_cluster(event):
        return markov_clusters[event]

    with open(filename, 'w') as mcl_file:
        for k,v in markov_chains.iteritems():
            if( map_event_to_cluster(k) == cluster_id ):
                for k2,v2 in markov_chains[k].iteritems():
                    if( map_event_to_cluster(k2) == cluster_id ):
                        first = k
                        second = k2
                        weight = v2["weight"]
                        mcl_file.write('{0}\t{1}\t{2}\n'.format(first,second,weight))
    
def compute_cluster_degrees(markov_chains, markov_clusters):
    nodes = collections.defaultdict(
            lambda: {"in":set(), "out":set()}) 

    def map_event_to_cluster(event):
        return markov_clusters[event]

    for k,v in markov_chains.iteritems():
        cluster_a = map_event_to_cluster(k)
        for k2,v2 in v.iteritems():
            cluster_b = map_event_to_cluster(k2)
            nodes[cluster_a]["out"].add( cluster_b  )
            nodes[cluster_b]["in"].add( cluster_a )

    result = {}
    for k,v in nodes.iteritems():
        result[k] = {
                "indegree": len(v["in"]),
                "outdegree": len(v["out"])
                }

    return result;


def go(query_response):
    #write_query_response(query_response, "data/mcl_input")
    run_mcl("data/mcl_input","data/mcl_output")
    markov_clusters = map_events_to_clusters("data/mcl_output")
    markov_chains, node_degrees = build_markov_chain("data/mcl_input", markov_clusters)
    markov_cluster_chains = build_markov_cluster_chain(markov_chains, markov_clusters)
    cluster_degrees = compute_cluster_degrees(markov_chains, markov_clusters)

    results = {
        'cluster_chains' : markov_cluster_chains,
        'chains' : markov_chains, 
        'node_degrees' : node_degrees,
        'cluster_degrees' : cluster_degrees,
    }

    return results


    print "processing complete."
    pprint.pprint(results)
