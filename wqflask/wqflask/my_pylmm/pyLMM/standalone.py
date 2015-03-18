# Standalone specific methods and callback handler
#
# Copyright (C) 2015  Pjotr Prins (pjotr.prins@thebird.nl)
#
# Set the log level with
#
#   logging.basicConfig(level=logging.DEBUG)

from __future__ import absolute_import, print_function, division

import numpy as np
import sys
import logging

# logger = logging.getLogger(__name__)
logger = logging.getLogger('lmm2')
logging.basicConfig(level=logging.DEBUG)
np.set_printoptions(precision=3,suppress=True)

def set_progress_storage(location):
    global storage
    storage = location
    
def progress(location, count, total):
    storage['percentage'] = round(count*100.0)/total)
    logger.info("Progress: %s %d%%" % (location,round(count*100.0/total)))

def mprint(msg,data):
    """
    Array/matrix print function
    """
    m = np.array(data)
    if m.ndim == 1:
        print(msg,m.shape,"=\n",m[0:3]," ... ",m[-3:])
    if m.ndim == 2:
        print(msg,m.shape,"=\n[",
              m[0][0:3]," ... ",m[0][-3:],"\n ",
              m[1][0:3]," ... ",m[1][-3:],"\n  ...\n ",
              m[-2][0:3]," ... ",m[-2][-3:],"\n ",
              m[-1][0:3]," ... ",m[-1][-3:],"]")

def callbacks():
    return dict(
        write = sys.stdout.write,
        writeln = print,
        debug = logger.debug,
        info = logger.info,
        warning = logger.warning,
        error = logger.error,
        critical = logger.critical,
        progress = progress,
        mprint = mprint
    )

def uses(*funcs):
    """
    Some sugar
    """
    return [callbacks()[func] for func in funcs]
    
# ----- Minor test cases:

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    logging.debug("Test %i" % (1))
    d = callbacks()['debug']
    d("TEST")
    wrln = callbacks()['writeln']
    wrln("Hello %i" % 34)
    progress = callbacks()['progress']
    progress("I am half way",50,100)
    list = [0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15,
            0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15,
            0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15,
            0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15,
            0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15]
    mprint("list",list)
    matrix = [[1,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15],
            [2,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15],
            [3,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15],
            [4,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15],
            [5,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15],
            [6,0.5,0.6096595 , -0.31559815, -0.52793285, 1.16573418e-15]]
    mprint("matrix",matrix)
    ix,dx = uses("info","debug")
    ix("ix")
    dx("dx")
