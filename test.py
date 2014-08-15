import json
import munger
import pprint

def main():
    query_response = read_test_response("test.json")
    results = munger.go(query_response)
    munger.write_results(results,"data/results.json")
    pprint.pprint(results)

def read_test_response(filename):
    with open(filename, 'r') as test_file:
        result = json.load(test_file)
    return result

if __name__ == '__main__':
    main()
