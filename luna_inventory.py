#!/usr/bin/env python

'''
Example custom dynamic inventory script for Ansible, in Python.
'''

import os
import sys
import argparse

import luna
try:
    import json
except ImportError:
    import simplejson as json

class LunaInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.luna_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory);

    def luna_inventory(self):
        inventory = {}
        inventory['_meta'] = { 'hostvars': {}}
        osimages = {'hosts':[],'vars': {'ansible_connection': 'chroot' }}
        for osimage in luna.list('osimage'):
            #osimages['hosts'].append(luna.OsImage(osimage).get('path'))
            osimages['hosts'].append(osimage)
            inventory['_meta']['hostvars'][osimage]= {'ansible_host':luna.OsImage(osimage).get('path')}

        inventory['osimages'] = osimages
        nodes = {}
        for n in luna.list('node'):
            node = luna.Node(n)
            group = node.show()['group'].replace("[","").replace("]","")
            if group in inventory:
                inventory[group]['hosts'].append(node.show()['name'])
            else:
                inventory[group] = {'hosts':[node.show()['name']]}
            inventory['_meta']['hostvars'][node.show()['name']]={"bmc_ip":node.get_ip('BMC',version=4)}
            inventory['_meta']['hostvars'][node.show()['name']]["ansible_host"]=node.get_ip('BOOTIF',version=4)

        return inventory
    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

# Get the inventory.
LunaInventory()
