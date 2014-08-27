import argparse

import common
import munger
import bqi

# These refer to datasets available on Google BigQuery
DATASET_TEST = "[publicdata:samples.github_timeline]"
DATASET_REAL = "[githubarchive:github.timeline]"

def save_reply(prefix, parameters):
    jobId = parameters['ids']['jobId']
    projectId = parameters['ids']['projectId']
    filename = "%s-%s.json" % (projectId, jobId)
    common.write_json(parameters, "%s/%s" % (prefix, filename))

def munge_queries(id):
    print "Munging:", id
    common.use_set(id)
    model = munger.munge_model( common.read_most_recent('model') )
    state = munger.munge_state( common.read_most_recent('state') )

    results = {"state":state, "model":model}
    common.write_json(results, "results.json")

def run_queries(setId, projectId, templates):
    project = bqi.get_bigquery_service(projectId)
    print "Using projectId:", project.projectId 
    print "Local Id:", setId

    common.use_set(setId)

    split_args = [arg.split(':') for arg in templates]
    named_args = {arg[0]:arg[1] for arg in split_args}

    for name, filename in named_args.iteritems():
        query = bqi.insert_query(project, name, filename, DATASET_TEST)
        reply = bqi.await_reply(project, query )
        reply = bqi.read_reply(project, query )
        save_reply( name, reply )

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-i", "--id", 
            required=True,
            help="identifier for this set")
    group = parser.add_argument_group("new query") 
    group.add_argument(
            "-q", "--query",
            help="use bigquery",
            dest="query",
            nargs="+")
    return parser

if __name__ == '__main__':
    parser = get_arguments()
    args = parser.parse_args()
    if (args.query is not None):
        projectId = args.query.pop(0)
        run_queries(args.id, projectId, args.query)
    munge_queries(args.id)
