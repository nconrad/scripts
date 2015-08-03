#!/usr/bin/env python
#
#   This script takes tab delimited (excel) file and produces a json table
#
#   Usage:
#       ./parse-file.py <input_path> <output_path>
#


import sys
import json

if __name__ == "__main__":
    lines = open(sys.argv[1], "r").read().splitlines();

    # get columns, remove any leading and trailing spaces
    columns = [item.strip() for item in lines[0].split('\t')]

    rows = []
    for line in lines:
        items = [item.strip() for item in line.split('\t')]

        obj = {}
        for i, item in enumerate(items):
            obj[columns[i]] = item;

        rows.append(obj)


    # write json
    if sys.argv[2] in ['.', '..', './', '../']:
        out_file = sys.argv[1].split('/')[-1]
    else:
        out_file = sys.argv[2]

    with open(out_file, 'w') as f:
        json.dump(rows, f)

    print '\ndone'