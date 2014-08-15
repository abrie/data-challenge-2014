import httplib2
import pprint
import sys
import json
import subprocess

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

# Enter your Google Developer Project number
PROJECT_NUMBER = 'linear-quasar-662'


def main():
    query_response = do_query("query.sql")
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

    write_results(results, 'data/results.json')

    print "processing complete."
    pprint.pprint(results)

def do_query(query_filename):
    FLOW = flow_from_clientsecrets('client_secrets.json', 
            scope='https://www.googleapis.com/auth/bigquery')
    storage = Storage('bigquery_credentials.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        from oauth2client import tools
        # Run oauth2 flow with default arguments.
        credentials = tools.run_flow(FLOW, storage, tools.argparser.parse_args([]))

    http = httplib2.Http()
    http = credentials.authorize(http)

    bigquery_service = build('bigquery', 'v2', http=http)

    with open (query_filename, "r") as query_file:
        bql=query_file.read()
    try:
        query_job = bigquery_service.jobs()
        query_body = {'query':bql}
        query_request = query_job.query(projectId=PROJECT_NUMBER, body=query_body)
        query_response = query_request.execute()

    except HttpError as err:
        print 'HttpError:', pprint.pprint(err.content)

    except AccessTokenRefreshError:
        print ("Credentials have been revoked or expired, please re-run the application to re-authorize")

    print query_response
    try:
        while not query_response['jobComplete']:
            query_response = query_job.getQueryResults(
                    projectId=query_response['jobReference']['projectId'],
                    jobId=query_response['jobReference']['jobId'])
    except:
        print "Unexpected error:", sys.exc_info()[0], query_response
        raise
        
    print "projectId: " + query_response['jobReference']['projectId']
    print "jobId: " + query_response['jobReference']['jobId'] 
    print "cacheHit:" + str(query_response['cacheHit'])
    print str( query_response['totalRows'] ) + " rows retrieved."

    return query_response

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


if __name__ == '__main__':
    main()
