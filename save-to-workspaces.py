#!/usr/bin/env python
#
#   Usage:
#       ./save-to-workspaces.py -h
#
#   Example:
#        ./save-to-workspaces.py --include-only .png --dir ../some/dir/ --ws /username/models/ecoli/
#

import io
import json
import sys
import os
import base64
import argparse
from api.patric import workspace as wsclient


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--skip', help="skip any file with substring match")
parser.add_argument('-i', '--include-only', help="only include files with this substring match")
parser.add_argument('-f', '--file', help="file to upload")
parser.add_argument('-d', '--dir', help="directory to upload")
parser.add_argument('-w', '--ws', help="workspace path where files will be saved")
args = parser.parse_args()


with open(os.environ['HOME'] + '/.rastauth') as file:
    token = file.read()

ws = wsclient.Workspace(token=token);           #patric

def save_all():
    print '\n\n*** Saving all files  ***\n'

    os.chdir(args.dir)

    for name in os.listdir(os.getcwd()):

        # skip any names that don't have substring for --include-only option
        if (args.include_only and args.include_only not in name):
            continue

        # skip any substring matches for --skip option
        if (args.skip and any(sub in name for sub in args.skip.split(',') ) ):
            print 'skipping:', name
            continue

        with open(name, "rb") as f:
            encoded_string = base64.b64encode(f.read())

        print 'saving:', args.ws+name
        test = ws.create({'objects': [[args.ws+name, 'png', {}, encoded_string]], 'overwrite': True})

        print


if __name__ == "__main__":

    if (args.file):
        pass
    if (args.dir):
        save_all()

    print 'Done.'



