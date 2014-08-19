import json
import munger
import pprint

def main():
    query_responses = [
            read_test_response("test-a.json"),
            read_test_response("test-b.json")]
    results = munger.munge(query_responses)
    munger.write_results(results,"data/results.json")
    pprint.pprint(results)

def read_test_response(filename):
    with open(filename, 'r') as test_file:
        result = json.load(test_file)
    return result

if __name__ == '__main__':
    main()
