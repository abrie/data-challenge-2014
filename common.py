import os, errno
import json

def datadir(path):
    base = "data/"
    return os.path.join(base,path) 

def write_json(data, path):
    directory = os.path.dirname(path) 
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(path, "w") as output_file:
        pretty_json = json.dumps(data, indent=4, sort_keys=True )
        output_file.write(pretty_json)
