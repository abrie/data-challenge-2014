#!/usr/bin/python
import argparse
import sys

import common
import munger
import bqi

# These refer to datasets available on Google BigQuery
DATASET_TEST = "[publicdata:samples.github_timeline]"
DATASET_REAL = "[githubarchive:github.timeline]"

def save_reply(prefix, parameters):
    job_id = parameters['ids']['jobId']
    project_id = parameters['ids']['projectId']
    filename = "%s-%s.json" % (project_id, job_id)
    common.write_json(parameters, "%s/%s" % (prefix, filename))

def munge_queries(set_id):
    print "Munging set_id:", set_id
    common.use_set(set_id)
    model = munger.munge_model(common.read_most_recent('model'))
    state = munger.munge_state(common.read_most_recent('state'))

    results = {"state":state, "model":model}
    common.write_json(results, "results.json")

def run_queries(set_id, project_id, templates):
    project = bqi.get_bigquery_service(project_id)
    print "Using project id:", project.project_id
    print "Local Id:", set_id

    common.use_set(set_id)

    split_args = [arg.split(':') for arg in templates]
    named_args = {arg[0]:arg[1] for arg in split_args}

    for name, filename in named_args.iteritems():
        query = bqi.insert_query(project, filename, DATASET_TEST)
        if "error" in query:
            print query["error"]["message"]
            return False
        else:
            reply = bqi.await_reply(project, query)
            reply = bqi.read_reply(project, query)
            save_reply(name, reply)
    return True

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id",
                        required=True,
                        help="identifier for this set")
    group = parser.add_argument_group("new query")
    group.add_argument("-q", "--query",
                       help="use bigquery",
                       dest="query",
                       nargs="+")
    return parser.parse_args()

def main():
    args = get_arguments()

    if args.query is not None:
        project_id = args.query.pop(0)
        if not run_queries(args.id, project_id, args.query):
            print "Refusing to munge because because queries failed."
            return False

    munge_queries(args.id)
    print "Done."
    return True

if __name__ == '__main__':
    try:
        if main():
            sys.exit(0)
        else:
            sys.exit(-1)

    except KeyboardInterrupt:
        print "Aborted - but queries may have been sent anyway."
