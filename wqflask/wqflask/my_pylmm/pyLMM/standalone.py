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

progress_location = None 
progress_current  = None
progress_prev_perc     = None

def progress_default_func(location,count,total):
    global progress_current
    value = round(count*100.0/total)
    progress_current = value
    
progress_func = progress_default_func

def progress_set_func(func):
    global progress_func
    progress_func = func
    
def progress(location, count, total):
    global progress_location
    global progress_prev_perc
    
    perc = round(count*100.0/total)
    if perc != progress_prev_perc and (location != progress_location or perc > 98 or perc > progress_prev_perc + 5):
        progress_func(location, count, total)
        logger.info("Progress: %s %d%%" % (location,perc))
        progress_location = location
        progress_prev_perc = perc

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

def fatal(msg):
    logger.critical(msg)
    raise Exception(msg)

def callbacks():
    return dict(
        write = sys.stdout.write,
        writeln = print,
        debug = logger.debug,
        info = logger.info,
        warning = logger.warning,
        error = logger.error,
        critical = logger.critical,
        fatal = fatal,
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
