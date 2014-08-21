import datetime
import os, errno
import json
import string
import random

base = "unset"

def new_set():
    global base
    # http://stackoverflow.com/a/2257449
    def generate_id(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    id = generate_id(3, "XAMURO")
    time = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    base = "".join(['data/', id, time,'/'])
    create_path(base)
    return base

def use_set(name):
    global base
    base = name

def read_all():
    path = datadir('query-responses')
    result = []
    for dir_entry in os.listdir(path):
        dir_entry_path = os.path.join(path, dir_entry)
        if os.path.isfile(dir_entry_path):
            with open(dir_entry_path, 'r') as my_file:
                result.append( json.load(my_file) )
    return result

def datadir(path):
    global base
    return os.path.join(base,path) 

def create_path(path):
    directory = os.path.dirname(path) 
    if not os.path.exists(directory):
        os.makedirs(directory)

def write_json(data, path):
    create_path(path)
    with open(path, "w") as output_file:
        pretty_json = json.dumps(data, indent=4, sort_keys=True )
        output_file.write(pretty_json)
