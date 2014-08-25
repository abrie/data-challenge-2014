import argparse
import string

def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--desc", required=True, help="description html")
    parser.add_argument("-i", "--id", required=True, help="results id")
    parser.add_argument("-t", "--template", required=True, help="template for a page")
    parser.add_argument("-o", "--out", required=True, help="write destination")
    return parser

def generate(template_filename, description_filename, data_id, output_filename):
    print "processing:", template_filename, description_filename, data_id, output_filename
    data_description = "none"
    with open (description_filename, "r") as description_file:
        data_description = description_file.read()

    with open (template_filename, "r") as template_file:
        template = string.Template(template_file.read()) 

    result = template.safe_substitute(data_description=data_description, data_id=data_id)

    with open (output_filename, "w") as output_file:
        output_file.write(result)

if __name__ == '__main__':
    parser = get_argument_parser()
    args = parser.parse_args()
    generate(args.template, args.desc, args.id, args.out)
