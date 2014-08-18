import httplib2
import json
import pprint
import string
import sys
import munger

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

# Enter your Google Developer Project number
PROJECT_NUMBER = 'linear-quasar-662'
TEST_DATASET = "[publicdata:samples.github_timeline]"
REAL_DATASET = "[githubarchive:github.timeline], [githubarchive:github.2011]"

#this code was found after much struggle at:
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

def do_query(bigquery_service, query_filename, dataset):
    with open (query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read()) 

    bql = bql_template.substitute(dataset=dataset)

    query_job = bigquery_service.jobs()
    query_body = {'query':bql}
    query_request = query_job.query(projectId=PROJECT_NUMBER, body=query_body)
    query_response = query_request.execute()

    return query_response

def process_query_responses(query_responses):
    for index, query_response in enumerate(query_responses):
        print "processing: %i of %i" % (index+1, len(query_responses))
        process_query_response(query_response)
        save_query_response(query_response, "data/query-response.json")

def process_query_response(query_response):
    while not query_response['jobComplete']:
        query_response = query_job.getQueryResults(
                projectId=query_response['jobReference']['projectId'],
                jobId=query_response['jobReference']['jobId'])

    print "projectId: " + query_response['jobReference']['projectId']
    print "jobId: " + query_response['jobReference']['jobId'] 
    print "cacheHit:" + str(query_response['cacheHit']) 
    print "totalBytesProcessed:" + query_response['totalBytesProcessed']
    print str( query_response['totalRows'] ) + " rows retrieved."

def save_query_response(query_response, query_response_filename):
    with open(query_response_filename, "w") as query_result_file:
        pretty_json = json.dumps(query_response, indent=4, sort_keys=True )
        query_result_file.write(pretty_json)

def munge_query_responses(query_responses):
    for index, query_response in enumerate(query_responses):
        print "munging %i of %i..." % (index+1, len(query_responses))
        results = munger.munge(query_response)
        munger.write_results(results, 'data/results.json')

def main():
    bigquery_service = get_bigquery_service()
    query_responses = [];
    query_responses.append(
            do_query(bigquery_service, "query.sql", TEST_DATASET))
    query_responses.append(
            do_query(bigquery_service, "query.sql", TEST_DATASET))
    process_query_responses(query_responses)
    munge_query_responses(query_responses)

if __name__ == '__main__':
    try:
        main()
    except HttpError as err:
        print 'HttpError:', pprint.pprint(err.content)

    except AccessTokenRefreshError:
        print ("Credentials have been revoked or expired, please re-run the application to re-authorize")
