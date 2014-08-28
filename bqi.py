import httplib2
import json
import os
import string
import sys

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

#https://developers.google.com/bigquery/bigquery-api-quickstart#completecode
def get_bigquery_service(project_id):
    if not os.path.isfile('client_secrets.json'):
        print "No client_secrets.json found."
        print "Please generate one of type 'Installed Applicaton'"
        return None

    scope = 'https://www.googleapis.com/auth/bigquery'
    client_secrets = "client_secrets.json"
    flow = flow_from_clientsecrets(client_secrets, scope=scope)
    storage = Storage('bigquery_credentials.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        from oauth2client import tools
        # Run oauth2 flow with default arguments.
        credentials = tools.run_flow(flow,
                                     storage,
                                     tools.argparser.parse_args([]))

    http = httplib2.Http()
    service = build('bigquery', 'v2', http=credentials.authorize(http))

    class BigQuery:
        def __init__(self, service, project_id):
            self.service = service
            self.project_id = project_id

    return BigQuery(service, project_id)

def insert_query(bigquery, query_filename, dataset):
    print "* async request:", dataset
    with open(query_filename, "r") as query_file:
        bql_template = string.Template(query_file.read())

    bql = bql_template.substitute(dataset=dataset)
    body = {'configuration':{'query':{'query':bql}}}
    parameters = {"ids": {"projectId": bigquery.project_id}}
    insert_params = {'projectId':bigquery.project_id, 'body':body}
    insert_request = bigquery.service.jobs().insert(**insert_params)

    try:
        inserted_query = insert_request.execute()
        parameters["ids"]["jobId"] = inserted_query['jobReference']['jobId']
    except HttpError as err:
        err_json = json.loads(err.content)
        parameters["error"] = err_json["error"]

    return parameters

def await_reply(bigquery, parameters):
    jobs = bigquery.service.jobs()
    ids = parameters['ids']
    sys.stdout.write("Awaiting: %s [..." % ids["jobId"])
    sys.stdout.flush()

    resultsRequest = jobs.getQueryResults(**ids)

    while True:
        reply = resultsRequest.execute()
        if reply['jobComplete']:
            break
        else:
            sys.stdout.write('...')
            sys.stdout.flush()

    sys.stdout.write("done]\n")
    sys.stdout.flush()

    parameters["reply"] = [reply]
    return parameters

def read_reply(bigquery, parameters):
    jobs = bigquery.service.jobs()
    ids = parameters["ids"]
    reply = parameters['reply'][0]
    total_rows = int(reply['totalRows'])
    rows_read = len(reply["rows"])
    request_params = {"projectId":ids["projectId"], "jobId":ids["jobId"]}
    while True:
        print "\tread %i of %s rows." % (rows_read, total_rows)
        if rows_read >= total_rows:
            break
        request_params["startIndex"] = rows_read
        request = jobs.getQueryResults(**request_params)
        reply = request.execute()
        parameters['reply'].append(reply)
        rows_read += len(reply["rows"])
    return parameters
