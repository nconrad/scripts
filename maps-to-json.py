#!/usr/bin/env python
#
#   Usage:
#       ./maps-to-json.py [save|save-all|convert] <file_name|directory> <workspace_path>
#
#   Params:
#       save        : for saving a single file to kbase/patric workspaces,
#                     must specify <file_name> (pending)
#       save-all    : for saving entire directory to kbase/patric workspaces (pending),
#                     must specify <directory> and <workspace_path>
#       convert     : convert a directory of kgml to modelseed-ready JSON,
#                     must specify <directory>
#

import io
import json
import sys
import os
from xml.dom import minidom

from api.patric import workspace as wsclient
#from api.kbase import workspace as wsclient

with open(os.environ['HOME'] + '/.rastauth') as file:
    token = file.read()
    print '\n Token: ', token



#fba = fbaclient.fbaModelServices('http://kbase.us/services/KBaseFBAModeling'); #kbase

ws = wsclient.Workspace(token=token);           #patric
#ws = wsclient.Workspace();                                                     #kbase



# this is the kegg rxn/cpds to seed mapping json files.
with open('mappings/rxn_mapping.json') as file:
    json_str = file.read()
    rxn_mapping = json.loads(json_str)

with open('mappings/cpd_mapping.json') as file:
    json_str = file.read()
    cpd_mapping = json.loads(json_str)

MAPSJSON = []




def graph_to_json(file_name):
    print 'Converting graph data from file:', file_name

    try:
        xmldoc = minidom.parse(file_name)
    except:
        sys.stderr.write("could not parse xml file: "+file_name+'\n')
        return


    itemlist = xmldoc.getElementsByTagName('pathway')

    try:
        name = itemlist[0].attributes['title'].value
    except:
        name = "None"

    map_number = itemlist[0].attributes['number'].value


    link = itemlist[0].attributes['link'].value

    json_obj = {'id': 'map'+map_number,
                'name': name,
                'link': link,
                'source_id': 'map'+map_number,
                'source': 'KEGG',
                'reactions':[],
                'compounds':[],
                'reaction_ids': [],
                'compound_ids': [],
                'linkedmaps': []
                }

    entries = xmldoc.getElementsByTagName('entry')
    reaction_ids = []
    compound_ids = []

    for obj in entries:
        if (obj.attributes['type'].value == 'group'):
            continue

        if (obj.attributes['type'].value == 'map'):
            e_obj = obj.attributes
            g_obj = obj.getElementsByTagName('graphics')[0].attributes

            obj = {"id": e_obj['id'].value,
                   "shape": g_obj['type'].value,
                   "name": g_obj['name'].value,
                   "h": int(g_obj['height'].value),
                   "w": int(g_obj['width'].value),
                   "x": int(g_obj['x'].value),
                   "y": int(g_obj['y'].value),
                  }
            name = e_obj['name'].value;

            if 'ec' in name:
                name = name.split('ec')[1]
            elif 'map' in name:
                name = name.split('map')[1]

            obj['map_id'] = 'map'+name
            obj['map_ref'] = 'map'+name


            json_obj['linkedmaps'].append(obj)
            continue



        if (obj.attributes['type'].value == 'enzyme'
            and obj.getElementsByTagName('graphics')):

            try:
                obj.attributes['reaction'].value
            except:
                continue

            e_obj = obj.attributes

            # get list of kegg rxn ids from the entry
            kegg_rxns = e_obj['reaction'].value \
                           .replace('rn:','').split(' ')


            reactions = xmldoc.getElementsByTagName('reaction')  # substrate and product data from kgml
            # for each kegg_rxn, get the seed rxn id, add to list
            rxns = []
            for kegg_rxn in kegg_rxns:
                try:
                    rxn_id = rxn_mapping[kegg_rxn]
                except:
                    #sys.stderr.write("Warning: [Converting "+file_name+
                    #    "] Could not find seed rxn id for KEGG id: "+kegg_rxn+'\n')
                    rxn_id = kegg_rxn
                rxns.append(rxn_id)

                reaction_ids.append(rxn_id)

                for reaction in reactions:

                    r_obj = reaction.attributes
                    #rn_ids = r_obj['name'].value.split(' ')
                    #rn_ids = [id.split(':')[1] for id in rn_ids]
                    #print rn_ids

                    if r_obj['id'].value == e_obj['id'].value:
                        if r_obj['type'].value == 'reversible':
                            reversible = 1
                        else:
                            reversible = 0

                        substrates = []
                        for substrate in reaction.getElementsByTagName('substrate'):
                            s_obj = {'compound_ref': substrate.attributes['name'].value.split(':')[1],
                                    'id': int(substrate.attributes['id'].value)}
                            substrates.append(s_obj)
                            #substrates.append(substrate.attributes['name'].value.split(':')[1]
                            #    +'/'+substrate.attributes['id'].value)
                        products = []
                        for product in reaction.getElementsByTagName('product'):
                            p_obj = {'compound_ref':  product.attributes['name'].value.split(':')[1],
                                     'id': int(product.attributes['id'].value)}
                            products.append(p_obj)
                            #products.append(product.attributes['name'].value.split(':')[1]
                            #    +'/'+product.attributes['id'].value)
                        break

                    #json_obj['arrows'].append(obj)


            g_obj = obj.getElementsByTagName('graphics')[0].attributes

            try:
                link = e_obj['link'].value
            except:
                #sys.stderr.write("Warning: [Converting "+file_name+
                #    "] Could not find link for reaction: "+kegg_rxn+'\n')
                pass

            x = y = h = w = False
            try:
                x = int(g_obj['x'].value)
                y = int(g_obj['y'].value)
                h = int(g_obj['height'].value)
                w = int(g_obj['width'].value)
            except:
                #sys.stderr.write("Warning: [Converting "+file_name+
                #    "] Could not find coordinates for reaction: "+kegg_rxn+'\n')
                pass

            obj = {"id": e_obj['id'].value,
                    "rxns": rxns,
                   "ec": e_obj['name'].value,
                   "shape": g_obj['type'].value,
                   "name": g_obj['name'].value,
                   }
            try:
                if substrates:
                    obj['substrate_refs'] = substrates
            except:
                obj['substrate_refs'] = []
                #sys.stderr.write("Warning: [Converting "+file_name+
                #    "] Could not find substrates and products for: "+kegg_rxn+'\n')

            try:
                if products:
                    obj['product_refs'] = products
            except:
                obj['product_refs'] = []
                #sys.stderr.write("Warning: [Converting "+file_name+
                #    "] Could not find substrates and products for: "+kegg_rxn+'\n')

            try:
                obj['reversible'] = reversible
            except:
                obj['reversible'] = 0
                #sys.stderr.write("Warning: [Converting "+file_name+
                #    "] Could not find type (reversibility) for: "+kegg_rxn+'\n')

            if link: obj['link'] = link

            if x: obj['x'] = x
            else: obj['x'] = 0
            if y: obj['y'] = y
            else: obj['y'] = 0
            if h: obj['h'] = h
            else: obj['h'] = 0
            if w: obj['w'] = w
            else: obj['w'] = 0

            json_obj['reactions'].append(obj)

        elif (obj.attributes['type'].value == 'compound'
            and obj.getElementsByTagName('graphics') ):

            e_obj = obj.attributes

            kegg_cpds = e_obj['name'].value \
                           .replace('cpd:','').split(' ')


            # for each kegg_cpd, get the seed cpd id, add to list
            cpds = []
            for kegg_cpd in kegg_cpds:

                try:
                    # replace this with seed mapping result in future
                    cpd_id = cpd_mapping[kegg_cpd]  #  get seed_id
                    label = fba.get_compounds({'compounds': [cpd_id]})[0]['name']
                    #print label
                except:
                    #sys.stderr.write("Warning: [Converting "+file_name+
                    #    "] Could not find seed cpd id for KEGG id: "+kegg_cpd+'\n')
                    cpd_id = kegg_cpd
                    label = 'No Label Available'

                cpds.append( cpd_id )

                compound_ids.append(cpd_id)

            g_obj = obj.getElementsByTagName('graphics')[0].attributes
            obj = {"id": e_obj['id'].value,
                   "name": g_obj['name'].value,
                   "label": label,
                   "cpds": cpds,
                   "ec": e_obj['name'].value,
                   "link": e_obj['link'].value,
                   "shape": g_obj['type'].value,
                   "x": int(g_obj['x'].value),
                   "y": int(g_obj['y'].value),
                   "h": int(g_obj['height'].value),
                   "w": int(g_obj['width'].value),
                   "link_refs": []       #fixme: I don't know what this is...
                   }

            json_obj['compounds'].append(obj)

        #print json_obj


    relations = xmldoc.getElementsByTagName('relation')

    for obj in relations:
        if (obj.attributes['type'].value == 'maplink'):

            entry1 = obj.attributes['entry1'].value
            entry2 = obj.attributes['entry2'].value

            for maplink in json_obj['linkedmaps']:
                maplink['connections'] = [entry1, entry2]




    json_obj['groups'] = getGroups(json_obj['reactions'])

    json_obj['reaction_ids'] = reaction_ids
    json_obj['compound_ids'] = compound_ids

    #print json_obj

    json_file = file_name.replace('.xml', '.json')
    outfile = open(json_file, 'w')
    json.dump(json_obj, outfile)
    print "Graph data converted to:", json_file
    print



def getGroups(rxns):
    groups = [];
    grouped_ids = [];

    #create groups
    for rxn in rxns:
        group = {'rxn_ids': []};

        #skip any reaction that has already been grouped
        if rxn['id'] in grouped_ids: continue

        group['rxn_ids'].append(rxn['id'])
        grouped_ids.append(rxn['id'])
        #group['id'] = len(grouped_ids)

        for rxn2 in rxns:
            #skip the reaction in question already
            if rxn2['id'] == rxn['id']: continue

            #skip any reaction that has already been grouped
            if rxn2['id'] in grouped_ids > 0: continue

            #if reactions share same substrates and products, add to group
            if (rxn['product_refs'] == rxn2['product_refs'] and
                    rxn['substrate_refs'] == rxn2['substrate_refs']):
                group['rxn_ids'].append(rxn2['id'])
                grouped_ids.append(rxn2['id'])
                #group['id'] = len(grouped_ids)

        groups.append(group)

    # get mid points and unique id of groups
    for group in groups:
        xs = []
        ys = []
        for rxn_id in group['rxn_ids']:
            for rxn in rxns:
                if rxn['id'] == rxn_id:
                    xs.append(rxn['x'])
                    ys.append(rxn['y'])



        x = (max(xs) + min(xs)) / 2
        y = (max(ys) + min(ys)) / 2

        group['x'] = x
        group['y'] = y

    return groups


def save_all(dir_name, ws_path):
    print '\n\n*** Saving all json objects  ***\n'

    os.chdir(dir_name)

    for name in os.listdir(os.getcwd()):
        if name.endswith('.json'):
            json_data = open(name)
            data = json.load(json_data)
            map_id = 'map'+name[2:7]

            print 'saving map: '+ws_path+map_id
            test = ws.create({'objects': [[ws_path+map_id, 'json', {}, data]], 'overwrite': True})

            print

#    for name in os.listdir(os.getcwd()):
#        if name.endswith('.json'):
#            json_data=open(name)
#            data = json.load(json_data)
#            map_id = 'map'+name[2:7]
#
#            print 'saving map: '+map_id
#            test= ws.save_objects({'workspace': 'test49',
#                    'objects': [{
#                        'data': data,
#                        'meta': {'reaction_ids': ','.join(data['reaction_ids']),
#                                     'compound_ids': ','.join(data['compound_ids']),
#                                     'name': data['name']},
#                        'type': 'KBaseBiochem.MetabolicMap'}
#                    ]})
#            print



# this function attempts to convert all .xml files in the current directory
def convert_all_data(dir_name):
    os.chdir(dir_name)

    print '\n\n*** Converting graph data ***\n'

    for name in os.listdir(os.getcwd()):
        if name.endswith('.xml'):
            graph_to_json(name)



if __name__ == "__main__":

    if (sys.argv[1] == 'save-all'):
        save_all(sys.argv[2], sys.argv[3])
    elif (sys.argv[1] == 'convert'):
        convert_all_data(sys.argv[2])

    #ws = wsclient.Workspace()
    # workspaces = ws.list_workspaces({})

    # for arr in workspaces:
    #     if str(arr[1]) != 'nconrad': continue

    #     print str(arr)  + '\n'

    #convert_all_data()

    # use one of these to convert a single file

    #data_to_json(sys.argv[1])
    #graph_to_json(sys.argv[1])

    print 'Done.'



