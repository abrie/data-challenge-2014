import httplib2
import os
import string
import sys

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

#https://developers.google.com/bigquery/bigquery-api-quickstart#completecode
def get_bigquery_service(projectId):
    if not os.path.isfile('client_secrets.json'):
        print "No client_secrets.json found."
        print "Please generate one of type 'Installed Applicaton'"
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

def insert_query(bigquery, prefix, query_filename, dataset):
    print "* async request:", dataset 
    with open (query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read()) 

    bql = bql_template.substitute(dataset=dataset)
    jobData = { 'configuration': { 'query':{ 'query':bql } } }
    insertParameters = {'projectId':bigquery.projectId, 'body':jobData}
    insertRequest = bigquery.service.jobs().insert( **insertParameters )

    try:
        insertedQuery = insertRequest.execute()
    except HttpError as err:
        err_json = json.loads(err.content)
        print '- HttpError Exception -'
        print "code:", err_json["error"]["code"] 
        print "message:", err_json["error"]["message"]
        parameters["error"] = err_json
    finally:
        parameters = {
                "ids": {
                    "jobId":insertedQuery['jobReference']['jobId'],
                    "projectId":bigquery.projectId}
                }

    return parameters

def await_reply( bigquery, parameters ):
    jobCollection = bigquery.service.jobs()
    ids = parameters['ids']
    sys.stdout.write("Awaiting: %s [..." % ids["jobId"])
    sys.stdout.flush()

    resultsRequest = jobCollection.getQueryResults(**ids)

    while True:
        reply = resultsRequest.execute()
        if reply['jobComplete']: break
        else:
            sys.stdout.write('...')
            sys.stdout.flush()

    sys.stdout.write("done]\n")
    sys.stdout.flush()

    parameters["reply"] = [reply];
    return parameters 

def read_reply(bigquery, parameters):
    jobCollection = bigquery.service.jobs()
    ids = parameters["ids"]
    reply = parameters['reply'][0]
    totalRows = int(reply['totalRows'])
    rowsRead = len(reply["rows"])
    requestParams = {"projectId":ids["projectId"], "jobId":ids["jobId"]}
    while True: 
        print "\tread %i of %s rows." % (rowsRead, totalRows)
        if rowsRead >= totalRows:
            break
        requestParams["startIndex"] = rowsRead 
        request = jobCollection.getQueryResults( **requestParams )
        reply = request.execute()
        parameters['reply'].append(reply)
        rowsRead += len(reply["rows"])
    return parameters
