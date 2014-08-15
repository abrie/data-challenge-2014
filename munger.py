import httplib2
import pprint
import sys
import json
import subprocess

def write_query_response(query_response, filename):
    with open(filename, 'w') as mcl_file:
        for row in query_response['rows']:
            fields = row['f'];
            first = fields[0]['v'];
            second = fields[1]['v'];
            count = fields[2]['v'];
            ratio = fields[3]['v'];
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

def build_markov_chain(filename):
    weights = {}
    chains = {}
    with open(filename, 'r') as mcl_file:
        for line in mcl_file.readlines():
            fields = line.rstrip('\n').split('\t')
            first = fields[0]
            second = fields[1]
            ratio = float(fields[2])
            if not chains.has_key(first):
                chains[first] = {}
            chains[first][second] = {"weight":ratio, "hits":1}
            if not weights.has_key(second):
                weights[second] = {"weight":0.0, "hits":0}
            weights[second]["weight"] += ratio
            weights[second]["hits"] += 1 
    return (chains, weights)

def build_markov_cluster_chain(event_chain, markov_clusters):
    result = {}

    def map_event_to_cluster(event):
        return markov_clusters[event]

    for event_a, target_events in event_chain.iteritems():
        cluster_id_a = map_event_to_cluster(event_a)
        if not result.has_key( cluster_id_a ):
            result[cluster_id_a] = {}
        for event_b, event_b_params in target_events.iteritems():
            cluster_id_b = map_event_to_cluster(event_b)
            if not result[cluster_id_a].has_key(cluster_id_b):
                result[cluster_id_a][cluster_id_b] = {"weight":0.0, "hits":0}
            result[cluster_id_a][cluster_id_b]["weight"] += event_b_params["weight"]
            result[cluster_id_a][cluster_id_b]["hits"] += event_b_params["hits"] 
    return result

def write_results(results, filename):
    with open(filename, 'w') as outfile:
        prettyJson = json.dumps(results, indent=4, sort_keys=True )
        outfile.write( prettyJson )

def go(query_response):
    write_query_response(query_response, "data/mcl_input")
    run_mcl("data/mcl_input","data/mcl_output")
    markov_clusters = map_events_to_clusters("data/mcl_output")
    markov_chains, markov_weights = build_markov_chain("data/mcl_input")
    markov_cluster_chains = build_markov_cluster_chain(markov_chains, markov_clusters)

    results = {
        'clusters' : markov_clusters,
        'cluster_chains' : markov_cluster_chains,
        'chains' : markov_chains, 
        'weights' : markov_weights,
    }

    return results


    print "processing complete."
    pprint.pprint(results)
