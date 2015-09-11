# WGCNA analysis for GN2
# Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>

from numpy import *
from pandas import *

import scipy as sp                            # SciPy
import rpy2.robjects as ro                    # R Objects
import pandas.rpy.common as com               # R common functions

from rpy2.robjects.packages import importr
utils = importr("utils")

## Get pointers to some common R functions
r_library       = ro.r["library"]             # Map the library function
r_options       = ro.r["options"]             # Map the options function
r_read_csv      = ro.r["read.csv"]            # Map the read.csv function
r_dim           = ro.r["dim"]                 # Map the dim function
r_c             = ro.r["c"]                   # Map the c function
r_seq           = ro.r["seq"]                 # Map the seq function
r_table         = ro.r["table"]               # Map the table function
r_names         = ro.r["names"]               # Map the names function
r_png           = ro.r["png"]                 # Map the png function for plotting
r_dev_off       = ro.r["dev.off"]             # Map the dev.off function


#TODO: This should only be done once, since it is quite expensive
print(r_library("WGCNA"))                     # Load WGCNA
print(r_options(stringsAsFactors = False))



class WGCNA(object):
    def __init__(self, start_vars):
        print("Initialization of WGCNA")

    def run_wgcna(self):
        print("Starting WGCNA analysis")

    def process_wgcna_results(self, results):
        print("Processing WGCNA output")

