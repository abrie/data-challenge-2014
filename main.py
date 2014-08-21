import argparse
import httplib2
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
PROJECT_NUMBER = 'directed-potion-651'

# These refer to datasets available on Google BigQuery
TEST_DATASET = "[publicdata:samples.github_timeline]"
REAL_DATASET = "[githubarchive:github.timeline], [githubarchive:github.2011]"

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
    http = credentials.authorize(http)

    bigquery_service = build('bigquery', 'v2', http=http)

    return bigquery_service


def queue_async_query(bigquery_service, query_filename, dataset, month):
    print "* async:", dataset, month 
    with open (query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read()) 

    bql = bql_template.substitute(dataset=dataset, month=month)

    jobCollection = bigquery_service.jobs()
    jobData = { 'configuration': { 'query':{ 'query':bql } } }

    query = jobCollection.insert(
            projectId=PROJECT_NUMBER,
            body=jobData).execute()

    return query  

def process_query_responses(bigquery_service, queries):
    jobCollection = bigquery_service.jobs()
    results = []
    for index, query in enumerate(queries):
        jobId = query['jobReference']['jobId']
        print "Processing response from: ", jobId
        reply = jobCollection.getQueryResults(
                jobId=jobId,
                projectId=PROJECT_NUMBER).execute()
        rows = [];
        while( ('rows' in reply) and len(rows) < reply['totalRows']):
            rows.extend(reply['rows'])
            print "read %i rows of %s." % (len(rows), reply['totalRows'])
            reply = jobCollection.getQueryResults(
                    jobId=jobId,
                    projectId=PROJECT_NUMBER,
                    startIndex=len(rows)).execute()

        result = {"rows":rows}
        log_query( query, result )
        results.append(result)

    return results

def log_query(query, query_response):
    query_jobId = query['jobReference']['jobId']
    common.write_json(query, common.datadir("queries/%s.json" % query_jobId))
    common.write_json(query_response, common.datadir("query-responses/%s.json" % query_jobId))

def use_precollected(path):
    common.use_set(path)
    results = common.read_all()
    results = munger.munge( results )
    common.write_json(results, common.datadir("results.json"))

def main(presaved):
    print "This is run:", common.new_set()
    bigquery_service = get_bigquery_service()
    queries = [];
    for month in range(0, 13):
        queries.append( queue_async_query(bigquery_service, "query.sql", TEST_DATASET, month) )
    results = process_query_responses(bigquery_service, queries)
    results = munger.munge( results )
    common.write_json(results, common.datadir("results.json"))

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--use", help="uses pregathered data")
    return parser.parse_args()

if __name__ == '__main__':
    try:
        args = get_arguments()
        if (args.use != None):
            use_precollected(args.use)
        else:
            main()
    except HttpError as err:
        print 'HttpError:', pprint.pprint(err.content)

    except AccessTokenRefreshError:
        print ("Credentials have been revoked or expired, please re-run the application to re-authorize")
