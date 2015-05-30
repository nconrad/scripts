#!/usr/bin/env python

# this script takes tab delimited (excel) file and produces a json table

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
    with open('output/'+sys.argv[1].split('/')[-1].replace('.txt', '_out.json'), 'w') as f:
        json.dump(rows, f)

    print '\ndone'