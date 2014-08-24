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

import numpy

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

# Enter your Google Developer Project number
#PROJECT_ID = 'glass-guide-678'
#PROJECT_ID = 'linear-quasar-662'
#PROJECT_ID = 'directed-potion-651'
PROJECT_ID = 'tough-pod-681'

# These refer to datasets available on Google BigQuery
DATASET_TEST = "[publicdata:samples.github_timeline]"
DATASET_REAL = "[githubarchive:github.timeline]"

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
    model = munger.munge_model( common.read_all('model') )
    state = {}
    #state = munger.munge_state( common.read_all('state') )
    times = munger.munge_times( common.read_all('times') )

    results = {"state":state, "model":model, "times":times}
    common.write_json(results, "results.json")

def run_new_query(model_query, state_query, time_query):
    print "Using project:", PROJECT_ID
    common.new_set()
    bigquery_service = get_bigquery_service()

    #run the model query
    model_queries = [];
    model = {}
    model_queries.append(
            queue_async_query(bigquery_service, 'model', model_query, DATASET_REAL) )
    process_query_responses(bigquery_service, 'model', model_queries)
    model = munger.munge_model( common.read_all('model') )

    #run the state queries
    state = {}
    #state_queries = [];
    #state_queries.append(
    #        queue_async_query(bigquery_service, 'state', state_query, DATASET_REAL) )
    #process_query_responses(bigquery_service, 'state', state_queries)
    #state = munger.munge_state( common.read_all('state') )

    #run the time query
    time_queries = [];
    times = {}
    time_queries.append(
            queue_async_query(bigquery_service, 'times', time_query, DATASET_REAL) )
    process_query_responses(bigquery_service, 'times', time_queries)
    times = munger.munge_times( common.read_all('times') )

    results = {"state":state, "model":model, "times":times}
    common.write_json(results, "results.json")

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--id", help="reuse a previous query")
    parser.add_argument("-qm", "--modelsql", help="sql file used for model query")
    parser.add_argument("-qs", "--statesql", help="sql file used for state query")
    parser.add_argument("-qt", "--timessql", help="sql file used for times query")
    return parser

if __name__ == '__main__':
    try:
        parser = get_arguments()
        args = parser.parse_args()
        if( args.id is None and args.modelsql is None and args.statesql is None and args.timessql is None):
            parser.error("what to do?")
        elif (args.id is not None):
            use_previous_query(args.id)
        elif (args.modelsql is not None and args.statesql is not None and args.timessql is not None ):
            run_new_query(args.modelsql, args.statesql, args.timessql)
        else:
            parser.error("-qm, -qs, and -qt arguments must be used together")

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
