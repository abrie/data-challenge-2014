import json

import common
import munger

def read_test_response(filename):
    with open(filename, 'r') as test_file:
        result = json.load(test_file)
    return result

def main():
    query_responses = [
            read_test_response("test-a.json"),
            read_test_response("test-b.json")]

    results = munger.munge(query_responses)
    common.write_json(results,common.datadir("results.json"))

if __name__ == '__main__':
    main()
