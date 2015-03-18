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

last_location = None
last_progress = 0

def set_progress_storage(location):
    global storage
    storage = location
    
def progress(location, count, total):
    global last_location
    global last_progress
    
    perc = round(count*100.0/total)
    # print(last_progress,";",perc)
    if perc != last_progress and (location != last_location or perc > 98 or perc > last_progress + 5):
        storage.store("percent_complete",perc)
        logger.info("Progress: %s %d%%" % (location,perc))
        last_location = location
        last_progress = perc

    
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
