# Genenetwork2 specific methods and callback handler
#
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
#

from __future__ import absolute_import, print_function, division

import sys
import logging

# logging.basicConfig(level=logging.DEBUG)

def progress(location, count, total):
    print("Progress: %s %i %i @%d%%" % (location,count,total,round(count*100.0/total)))

def callbacks():
    return dict(
        write = sys.stdout.write,
        writeln = print,
        debug = logging.debug,
        info = logging.info,
        warning = logging.warning,
        error = logging.error,
        critical = logging.critical,
        progress = progress
    )
    
# ----- Minor test cases:

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Test %i" % (1))
    d = callbacks()['debug']
    d("TEST")
    wrln = callbacks()['writeln']
    wrln("Hello %i" % 34)
    progress = callbacks()['progress']
    progress("I am half way",50,100)
