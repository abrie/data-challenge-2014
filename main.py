import httplib2
import pprint
import sys
import json

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

    while not query_response['jobComplete']:
        query_response = query_job.getQueryResults(
                projectId=query_response['jobReference']['projectId'],
                jobId=query_response['jobReference']['jobId'])

    print "projectId: " + query_response['jobReference']['projectId']
    print "jobId: " + query_response['jobReference']['jobId'] 
    print "cacheHit:" + str(query_response['cacheHit'])

    with open('mcl_input', 'w') as mcl_file:
        for row in query_response['rows']:
          fields = row['f'];
          first = fields[0]['v'];
          second = fields[1]['v'];
          count = fields[2]['v'];
          ratio = fields[3]['v'];
          mcl_file.write('{0}\t{1}\t{2}\n'.format(first,second,ratio))

    print str( query_response['totalRows'] ) + " rows retrieved."

    markov_map = {}
    with open('mcl_input', 'r') as mcl_file:
        for line in mcl_file.readlines():
            fields = line.rstrip('\n').split('\t')
            first = fields[0]
            second = fields[1]
            ratio = fields[2]
            if not markov_map.has_key(first):
                markov_map[first] = {}
            markov_map[first][second] = float(ratio)

    with open('results.json', 'w') as outfile:
      json.dump(markov_map, outfile)

  except HttpError as err:
    print 'HttpError:', pprint.pprint(err.content)

  except AccessTokenRefreshError:
    print ("Credentials have been revoked or expired, please re-run"
           "the application to re-authorize")
if __name__ == '__main__':
    main()
