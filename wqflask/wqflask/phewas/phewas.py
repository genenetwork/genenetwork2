# PheWAS analysis for GN2
# Author / Maintainer: Li Hao & Danny Arends <Danny.Arends@gmail.com>
import sys
from numpy import *
import scipy as sp                            # SciPy
import rpy2.robjects as ro                    # R Objects
import rpy2.rinterface as ri

from base.webqtlConfig import GENERATED_IMAGE_DIR
from utility import webqtlUtil                # Random number for the image
from utility import genofile_parser           # genofile_parser

import base64
import array
import csv
import itertools

from base import data_set
from base import trait as TRAIT

from utility import helper_functions
from utility.tools import locate

from rpy2.robjects.packages import importr
utils = importr("utils")

class PheWAS(object):
    def __init__(self):
        print("Initialization of PheWAS")
        print("Initialization of PheWAS done !")

    def run_analysis(self, requestform):
        print("Starting PheWAS analysis on dataset")
        print("Initialization of PheWAS done !")

    def process_results(self, results):
        print("Processing PheWAS output")
        template_vars = {}
        return(dict(template_vars))

