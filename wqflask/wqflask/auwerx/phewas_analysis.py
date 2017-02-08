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

r_library       = ro.r["library"]             # Map the library function
r_options       = ro.r["options"]             # Map the options function

class PheWAS(object):
    def __init__(self):
        print("Initialization of PheWAS")
        r_library("auwerx")  # Load the auwerx package - Should only be done once, since it is quite expensive
        r_options(stringsAsFactors = False)
        # Create the aligners
        r_download_BXD_geno = ro.r["download.BXD.geno"]                               # Map the create.Pheno_aligner function
        r_create_Pheno_aligner = ro.r["create.Pheno_aligner"]                         # Map the create.Pheno_aligner function
        r_create_SNP_aligner = ro.r["create.SNP_aligner"]                             # Map the create.SNP_aligner function
        r_calculate_all_pvalue_parallel = ro.r["calculate.all.pvalue.parallel"]       # Map the calculate.all.pvalue.parallel function
        r_PheWASManhattan = ro.r["PheWASManhattan"]                                   # Map the PheWASManhattan function
        print("Initialization of PheWAS done !")

    def run_analysis(self, requestform):
        print("Starting PheWAS analysis on dataset")
        bxdgeno = r_download_BXD_geno()
        snpaligner = r_create_SNP_aligner(bxdgeno)
        phenoaligner = r_create_Pheno_aligner()
        allpvalues = r_calculate_all_pvalue_parallel()                                  # This needs some magic to work I think
        # trait chromosome and trait positions should come from the user input
        r_PheWASManhattan(None, allpvalues, phenoaligner, snpaligner, None, trait_chr, trait_pos, trait_pos )
        print("Initialization of PheWAS done !")

    def process_results(self, results):
        print("Processing PheWAS output")
        template_vars = {}
        return(dict(template_vars))

