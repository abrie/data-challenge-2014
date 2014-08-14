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

FLOW = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/bigquery')

def main():
    storage = Storage('bigquery_credentials.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        from oauth2client import tools
        # Run oauth2 flow with default arguments.
        credentials = tools.run_flow(FLOW, storage, tools.argparser.parse_args([]))

    http = httplib2.Http()
    http = credentials.authorize(http)

    bigquery_service = build('bigquery', 'v2', http=http)

    with open ("query.sql", "r") as query_file:
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

    with open('data/mcl_input', 'w') as mcl_file:
        for row in query_response['rows']:
          fields = row['f'];
          first = fields[0]['v'];
          second = fields[1]['v'];
          count = fields[2]['v'];
          ratio = fields[3]['v'];
          mcl_file.write('{0}\t{1}\t{2}\n'.format(first,second,ratio))

    print str( query_response['totalRows'] ) + " rows retrieved."
    print "----invoking mcl----"
    try:
        subprocess.check_call(["mcl/bin/mcl","data/mcl_input","-I","5.0","--abc", "-o","data/mcl_output"])
    except CalledProcessError as err:
        print 'CalledProcessError:', pprint.pprint(err)
    print "----mcl completed----"
    
    markov_clusters = {}
    with open('data/mcl_output', 'r') as mcl_output:
        for index, line in enumerate( mcl_output.readlines() ):
            fields = line.rstrip('\n').split('\t')
            cluster_id = "cluster_%i" % index
            for field in fields:
                markov_clusters[field] = "cluster_%i" % index 

    markov_weights = {}
    markov_chains = {}
    with open('data/mcl_input', 'r') as mcl_file:
        for line in mcl_file.readlines():
            fields = line.rstrip('\n').split('\t')
            first = fields[0]
            second = fields[1]
            ratio = float(fields[2])
            if not markov_chains.has_key(first):
                markov_chains[first] = {}
            markov_chains[first][second] = {"weight":ratio, "hits":1}
            if not markov_weights.has_key(second):
                markov_weights[second] = {"weight":0.0, "hits":0}
            markov_weights[second]["weight"] += ratio
            markov_weights[second]["hits"] += 1 

    def map_event_to_cluster(event):
        return markov_clusters[event]

    markov_cluster_chains = {}
    for event_a, target_events in markov_chains.iteritems():
        cluster_id_a = map_event_to_cluster(event_a)
        if not markov_cluster_chains.has_key( cluster_id_a ):
            markov_cluster_chains[cluster_id_a] = {}
        for event_b, event_b_params in target_events.iteritems():
            cluster_id_b = map_event_to_cluster(event_b)
            if not markov_cluster_chains[cluster_id_a].has_key(cluster_id_b):
                markov_cluster_chains[cluster_id_a][cluster_id_b] = {"weight":0.0, "hits":0}
            markov_cluster_chains[cluster_id_a][cluster_id_b]["weight"] += event_b_params["weight"]
            markov_cluster_chains[cluster_id_a][cluster_id_b]["hits"] += event_b_params["hits"] 

    result = {}
    with open('data/results.json', 'w') as outfile:
        result['clusters'] = markov_clusters
        result['cluster_chains'] = markov_cluster_chains
        result['chains'] = markov_chains 
        result['weights'] = markov_weights
        prettyJson = json.dumps(result, indent=4, sort_keys=True )
        outfile.write( prettyJson )

    print "processing complete."
    pprint.pprint(result)

if __name__ == '__main__':
    main()
