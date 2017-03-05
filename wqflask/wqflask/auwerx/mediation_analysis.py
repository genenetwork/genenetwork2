# PheWAS analysis for GN2
# Author / Maintainer: Li Hao & Danny Arends <Danny.Arends@gmail.com>

import sys
from numpy import *
import scipy as sp                            # SciPy
import rpy2.robjects as ro                    # R Objects
import rpy2.rinterface as ri

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

class Mediation(object):
    def __init__(self):
        print("Initialization of Mediation")
        print("Initialization of Mediation done !")

    def run_analysis(self, requestform):
        print("Starting Mediation analysis on dataset")
        print("Initialization of Mediation done !")

    def process_results(self, results):
        print("Processing Mediation output")
        template_vars = {}
        return(dict(template_vars))
