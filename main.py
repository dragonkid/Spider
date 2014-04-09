#!/usr/bin python
# -*- coding: UTF-8 -*-

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--verbosity", help="increase output verbosity",
                    action='store_true')
args = parser.parse_args()
if args.verbosity != 0:
    print type(args.verbosity)
    print "verbosity turned on"
else:
    print 'verbosity turned off'
