# Genenetwork2 specific methods and callback handler
#
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
#

from __future__ import absolute_import, print_function, division

import numpy as np
import sys
import logging

# logging.basicConfig(level=logging.DEBUG)
# np.set_printoptions()

def progress(location, count, total):
    """
    Progress update
    """
    logging.info("Progress: %s %d%%" % (location,round(count*100.0/total)))

def mprint(msg,data):
    """
    Array/matrix print function
    """
    m = np.array(data)
    print(msg,m.shape,"=\n",m)

def callbacks():
    return dict(
        write = sys.stdout.write,
        writeln = print,
        debug = logging.debug,
        info = logging.info,
        warning = logging.warning,
        error = logging.error,
        critical = logging.critical,
        progress = progress,
        mprint = mprint
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
