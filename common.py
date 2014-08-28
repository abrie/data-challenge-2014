"""Encapsulates saving/retrieving files from a 'SET' directory"""
import json
import os

ROOT = "data"
SET_ID = None

def use_set(id):
    global SET_ID
    SET_ID = id

def path(folder):
    global SET_ID
    return os.path.join(ROOT, SET_ID, folder)

def get_most_recent(folder):
    def ctimekey(filename):
        return os.path.getctime(os.path.join(path(folder), filename))
    most_recent = max(os.listdir(path(folder)), key=ctimekey)
    return os.path.join(path(folder), most_recent)

def read_most_recent(folder):
    most_recent = get_most_recent(folder)
    if os.path.isfile(most_recent):
        with open(most_recent, 'r') as most_recent_file:
            return json.load(most_recent_file)

def create_path(new_path_name):
    new_path_dir = os.path.dirname(path(new_path_name))
    if not os.path.exists(new_path_dir):
        os.makedirs(new_path_dir)

def read_json(filename):
    with open(path(filename), 'r') as my_file:
        return json.load(my_file)

def write_json(data, dest):
    create_path(dest)
    with open(path(dest), "w") as output_file:
        pretty_json = json.dumps(data, indent=4, sort_keys=True)
        output_file.write(pretty_json)
