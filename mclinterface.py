import pprint
import subprocess
import sys

import common

def write_model_to_mcl_input(model, filename):
    with open(filename, 'w') as mcl_file:
        for k,v in model.iteritems():
            for k2,v2 in model[k].iteritems():
                fields = (k,k2,v2['weight'])
                line = '%s\t%s\t%f\n' % fields
                mcl_file.write(line)

def map_states_to_clusters(input_filename):
    result = {}
    with open(common.datadir("mcl_output"), 'r') as mcl_output:
        for index, line in enumerate( mcl_output.readlines() ):
            fields = line.rstrip('\n').split('\t')
            cluster_id = "cluster_%i" % index
            for field in fields:
                result[field] = cluster_id 
    return result

def run_mcl(input_filename, output_filename):
    print "**** subprocess will call as follows:"
    call_parameters = [
            "mcl/bin/mcl", input_filename,
            "-I","5.0",
            "--abc",
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
    write_model_to_mcl_input(model, common.datadir("mcl_input"))
    run_mcl(common.datadir("mcl_input"),common.datadir("mcl_output"))
    return map_states_to_clusters(common.datadir("mcl_output"))
