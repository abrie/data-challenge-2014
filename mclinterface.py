import pprint
import subprocess
import sys

import common

MCL_BIN = "external/mcl-14-137/bin/mcl"

def write_model_to_mcl_input(model, filename):
    with open(filename, 'w') as mcl_file:
        for state_a in model.iterkeys():
            for state_b, transition in model[state_a].iteritems():
                fields = (state_a, state_b, transition['weight'])
                line = '%s\t%s\t%f\n' % fields
                mcl_file.write(line)

def map_states_to_clusters(input_filename):
    result = {}
    with open(common.path("mcl_output"), 'r') as mcl_output:
        for index, line in enumerate(mcl_output.readlines()):
            fields = line.rstrip('\n').split('\t')
            cluster_id = "cluster_%i" % (index)
            for field in fields:
                result[field] = cluster_id
    return result

def run_mcl(input_filename, output_filename):
    print "**** subprocess will call as follows:"
    call_parameters = [MCL_BIN, input_filename,
                       "-I", "6.0", #Inflation parameter
                       "--abc", #Input format
                       "-o", output_filename]
    pprint.pprint(call_parameters)

    print "**** calling..."

    try:
        subprocess.check_call(call_parameters)
    except subprocess.CalledProcessError as err:
        print 'Error while invoking MCL subprocess'
        pprint.pprint(err)
        sys.exit(1)

    print "**** subprocess completed ****"

def get_clusters(model):
    write_model_to_mcl_input(model, common.path("mcl_input"))
    run_mcl(common.path("mcl_input"), common.path("mcl_output"))
    return map_states_to_clusters(common.path("mcl_output"))
