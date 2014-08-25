import datetime
import os, errno
import json
import string
import random

dataroot = "data"
base = "UnSet!"

def is_initialized():
    global base
    return base != "UnSet!"

def new_set():
    global base
    # http://stackoverflow.com/a/2257449
    def generate_id(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    
    id = generate_id(3, "XAMURE")
    time = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    base = "%s-%s" % (id,time)

def use_set(id):
    global base
    base = id

def read_most_recent(prefix):
    result = []
    path = datadir(os.path.join(prefix,'query-responses'))
    cwd = os.getcwd()
    os.chdir(path)
    most_recent_file = max(os.listdir('.'), key=os.path.getctime)
    os.chdir(cwd)
    dir_entry_path = os.path.join(path, most_recent_file)
    if os.path.isfile(dir_entry_path):
        with open(dir_entry_path, 'r') as my_file:
            result.append( json.load(my_file) )
    return result

def read_all(prefix):
    path = datadir(os.path.join(prefix,'query-responses'))
    result = []
    for dir_entry in os.listdir(path):
        dir_entry_path = os.path.join(path, dir_entry)
        if os.path.isfile(dir_entry_path):
            with open(dir_entry_path, 'r') as my_file:
                result.append( json.load(my_file) )
    return result

def datadir(path):
    global base
    return os.path.join(dataroot,base,path) 

def create_path(path):
    directory = os.path.dirname(datadir(path)) 
    if not os.path.exists(directory):
        os.makedirs(directory)

def write_json(data,path):
    create_path(path)
    with open(datadir(path), "w") as output_file:
        pretty_json = json.dumps(data, indent=4, sort_keys=True )
        output_file.write(pretty_json)
