import argparse
import httplib2
import json
import os
import pprint
import string
import sys
import time

import common
import munger

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

# Enter your Google Developer Project number
PROJECT_ID = 'glass-guide-678'

# These refer to datasets available on Google BigQuery
DATASET_TEST = "[publicdata:samples.github_timeline]"
DATASET_UNION = "[githubarchive:github.timeline], [githubarchive:github.2011]"
DATASET_PRESENT = "[githubarchive:github.timeline]"
DATASET_2011 = "[githubarchive:github.2011]"

#https://developers.google.com/bigquery/bigquery-api-quickstart#completecode
def get_bigquery_service():
    FLOW = flow_from_clientsecrets('client_secrets.json', 
            scope='https://www.googleapis.com/auth/bigquery')
    storage = Storage('bigquery_credentials.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        from oauth2client import tools
        # Run oauth2 flow with default arguments.
        credentials = tools.run_flow(FLOW, storage, tools.argparser.parse_args([]))

    http = httplib2.Http()
    return build('bigquery', 'v2', http=credentials.authorize(http))

def queue_async_query(bigquery_service, prefix, query_filename, dataset):
    print "* async request:", dataset 
    with open (query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read()) 

    bql = bql_template.substitute(dataset=dataset)
    jobData = { 'configuration': { 'query':{ 'query':bql } } }
    insertParameters = {'projectId':PROJECT_ID, 'body':jobData}
    query = bigquery_service.jobs().insert( **insertParameters ).execute()
    save_query(prefix, query)
    return query

def process_query_responses(bigquery_service, prefix, queries):
    jobCollection = bigquery_service.jobs()
    for index, query in enumerate(queries):
        parameters = {
                "jobId":query['jobReference']['jobId'],
                "projectId":PROJECT_ID
                }
        sys.stdout.write("Awaiting: %s [" % parameters["jobId"])
        resultsRequest = jobCollection.getQueryResults(**parameters)
        while True:
            reply = resultsRequest.execute()
            if reply['jobComplete']: break
            sys.stdout.write('.')
        print "done]"

        rows = [];
        while( ('rows' in reply) and len(rows) < reply['totalRows']):
            rows.extend(reply['rows'])
            parameters["startIndex"] = len(rows);
            print "\tread %i/%s rows." % (len(rows), reply['totalRows'])
            reply = jobCollection.getQueryResults(**parameters).execute()

        save_query_result( prefix, query, {"rows":rows} )

def save_query(prefix, query):
    query_jobId = query['jobReference']['jobId']
    common.write_json(query, "%s/queries/%s.json" % (prefix, query_jobId))

def save_query_result(prefix, query, result):
    query_jobId = query['jobReference']['jobId']
    common.write_json(result, "%s/query-responses/%s.json" % (prefix, query_jobId))

def use_previous_query(id):
    print "Using previous query results from:", id
    common.use_set(id)
    results = common.read_all()
    results = munger.munge( results )
    common.write_json(results, common.datadir("results.json"))

def run_new_query(model_query, state_query):
    print "Using project:", PROJECT_ID
    common.new_set()
    bigquery_service = get_bigquery_service()

    #run the model query
    model_queries = [];
    model_queries.append(
            queue_async_query(bigquery_service, 'model', model_query, DATASET_UNION) )
    process_query_responses(bigquery_service, 'model', model_queries)
    model = munger.munge_model( common.read_all('model') )

    #run the state queries
    state_queries = [];
    state_queries.append(
            queue_async_query(bigquery_service, 'state', state_query, DATASET_UNION) )
    process_query_responses(bigquery_service, 'state', state_queries)

    state = munger.munge_state( common.read_all('state') )

    results = {"state":state, "model":model}
    common.write_json(results, "results.json")

def get_arguments():
    parser = argparse.ArgumentParser()

    modelgroup = parser.add_mutually_exclusive_group(required=True)
    modelgroup.add_argument("-p", "--previous", help="use a previous query")
    modelgroup.add_argument("-q", "--query", help="run a new query")

    stategroup = parser.add_mutually_exclusive_group(required=True)
    stategroup.add_argument("-ps", "--previouss", help="use a previous query")
    stategroup.add_argument("-qs", "--querys", help="run a new query")
    
    return parser.parse_args()

if __name__ == '__main__':
    try:
        args = get_arguments()
        if (args.previous != None):
            use_previous_query(args.previous, args.previouss)
        elif (args.query != None):
            run_new_query(args.query, args.querys)

    except HttpError as err:
        err_json = json.loads(err.content)
        print '- HttpError Exception -'
        print "code:", err_json["error"]["code"] 
        print "message:", err_json["error"]["message"]
        common.write_json(err_json, "error-fail-bad.json")

    except AccessTokenRefreshError:
        print ("Credentials have been revoked or expired, please re-run the application to re-authorize")

    finally:
        if common.is_initialized():
            print "Results logged to:", common.base
