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

# These refer to datasets available on Google BigQuery
DATASET_TEST = "[publicdata:samples.github_timeline]"
DATASET_REAL = "[githubarchive:github.timeline]"

#https://developers.google.com/bigquery/bigquery-api-quickstart#completecode
def get_bigquery_service(projectId):
    if not os.path.isfile('client_secrets.json'):
        print "No client_secrets.json found."
        print "Please use the Coogle developer console to generate one of type 'Installed Applicaton'"
        return None

    FLOW = flow_from_clientsecrets('client_secrets.json', 
            scope='https://www.googleapis.com/auth/bigquery')
    storage = Storage('bigquery_credentials.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        from oauth2client import tools
        # Run oauth2 flow with default arguments.
        credentials = tools.run_flow(FLOW, storage, tools.argparser.parse_args([]))

    http = httplib2.Http()
    service = build('bigquery', 'v2', http=credentials.authorize(http))

    class BigQuery:
        def __init__(self, service, projectId):
            self.service = service
            self.projectId = projectId

    return BigQuery(service, projectId) 

def queue_async_query(bigquery, prefix, query_filename, dataset):
    print "* async request:", dataset 
    with open (query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read()) 

    bql = bql_template.substitute(dataset=dataset)
    jobData = { 'configuration': { 'query':{ 'query':bql } } }
    insertParameters = {'projectId':bigquery.projectId, 'body':jobData}
    query = bigquery.service.jobs().insert( **insertParameters ).execute()
    save_query(prefix, query)
    return query

def process_query_responses(bigquery, prefix, queries):
    jobCollection = bigquery.service.jobs()
    for index, query in enumerate(queries):
        parameters = {
                "jobId":query['jobReference']['jobId'],
                "projectId":bigquery.projectId
                }
        sys.stdout.write("Awaiting: %s [..." % parameters["jobId"])
        sys.stdout.flush()
        resultsRequest = jobCollection.getQueryResults(**parameters)
        while True:
            reply = resultsRequest.execute()
            if reply['jobComplete']:
                break
            else:
                sys.stdout.write('...')
                sys.stdout.flush()
        sys.stdout.write("done]\n")
        sys.stdout.flush()

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
    print "Using most recent query results from:", id
    common.use_set(id)
    model = munger.munge_model( common.read_most_recent('model') )
    state = munger.munge_state( common.read_most_recent('state') )

    results = {"state":state, "model":model}
    common.write_json(results, "results.json")

def run_new_query(projectId, model_query, state_query, identifier):
    bigquery = get_bigquery_service(projectId)
    if bigquery is None:
        return

    print "Using project:", bigquery.projectId 

    if (identifier is None):
        common.new_set()
    else:
        common.use_set(identifier)


    #run the model query
    model_queries = [];
    model = {}
    model_queries.append(
            queue_async_query(bigquery, 'model', model_query, DATASET_TEST) )
    process_query_responses(bigquery, 'model', model_queries)
    model = munger.munge_model( common.read_all('model') )

    #run the state queries
    state = {}
    state_queries = [];
    state_queries.append(
            queue_async_query(bigquery, 'state', state_query, DATASET_TEST) )
    process_query_responses(bigquery, 'state', state_queries)
    state = munger.munge_state( common.read_all('state') )

    results = {"state":state, "model":model}
    common.write_json(results, "results.json")

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id", help="identifier for this query")
    parser.add_argument("-p", "--projectId", help="BigQuery projectId")
    group = parser.add_argument_group("query") 
    group.add_argument("--model")
    group.add_argument("--state")
    return parser

if __name__ == '__main__':
    try:
        parser = get_arguments()
        args = parser.parse_args()
        if (args.model is None and args.state is None):
            if (args.id is None):
                parser.error("nothing to do.")
            else:
                use_previous_query(args.id)
        elif (args.projectId is None):
            parser.error("please specify a Bigquery projectId to use.")
        else:
            run_new_query(args.projectId, args.model, args.state, args.id)

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
