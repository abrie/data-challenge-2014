import httplib2
import pprint
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

def main():
    query_response = do_query("query.sql")
    results = munger.go(query_response)
    munger.write_results(results, 'data/results.json')

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

if __name__ == '__main__':
    main()
