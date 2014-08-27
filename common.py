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
    path = datadir(prefix)
    def ctimekey(filename): 
        fullpath = os.path.join(path, filename)
        return os.path.getctime(fullpath)
    most_recent = max(os.listdir(path), key=ctimekey)
    path = os.path.join(path, most_recent)
    if os.path.isfile(path):
        with open(path, 'r') as most_recent_file:
            return json.load(most_recent_file)

def datadir(path):
    global base
    return os.path.join(dataroot,base,path) 

def create_path(path):
    directory = os.path.dirname(datadir(path)) 
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_json(filename):
    with open(datadir(filename), 'r') as my_file:
        return json.load(my_file)

def write_json(data,path):
    create_path(path)
    with open(datadir(path), "w") as output_file:
        pretty_json = json.dumps(data, indent=4, sort_keys=True )
        output_file.write(pretty_json)
