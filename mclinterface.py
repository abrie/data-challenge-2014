import pprint
import subprocess
import sys

def write_query_response(event_model, filename):
    with open(filename, 'w') as mcl_file:
        for k,v in event_model.iteritems():
            for k2,v2 in event_model[k].iteritems():
                fields = (k,k2,v2['weight'])
                line = '%s\t%s\t%f\n' % fields
                mcl_file.write(line)

def map_events_to_clusters(input_filename):
    result = {}
    with open('data/mcl_output', 'r') as mcl_output:
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
