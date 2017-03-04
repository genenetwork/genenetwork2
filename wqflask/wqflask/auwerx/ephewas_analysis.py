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

r_library       = ro.r["library"]             # Map the library function
r_options       = ro.r["options"]             # Map the options function
r_write_table   = ro.r["write.table"]         # Map the write.table function
r_head          = ro.r["head"]                # Map the head function
r_load          = ro.r["load"]                # Map the head function
r_colnames      = ro.r["colnames"]            # Map the colnames function
r_list          = ro.r["list"]                # Map the list function
r_c             = ro.r["c"]                   # Map the c (combine) function
r_print         = ro.r["print"]               # Map the print function
r_seq           = ro.r["seq"]                 # Map the rep (repeat) function

class EPheWAS(object):
    def __init__(self):
        print("Initialization of ePheWAS")
        print(r_library("auwerx"))                                                         # Load the auwerx package
        self.r_create_Pheno_aligner = ro.r["create.Pheno_aligner"]                         # Map the create.Pheno_aligner function
        self.r_data_gatherer = ro.r["data.gatherer"]                                       # Map the data.gatherer function
        print("Initialization of ePheWAS done !")

    def run_analysis(self, requestform):
        print("Starting ePheWAS analysis on dataset")
        genofilelocation = locate("BXD.geno", "genotype")                                  # Get the location of the BXD genotypes
        tissuealignerloc = locate("Tissue_color_aligner.csv", "auwerx")                       # Get the location of the Tissue_color_aligner

        # Get user parameters, trait_id and dataset, and store/update them in self
        self.trait_id = requestform["trait_id"]
        self.datasetname = requestform["dataset"]
        self.dataset = data_set.create_dataset(self.datasetname)

        # Print some debug
        print "self.trait_id:" + self.trait_id + "\n"
        print "self.datasetname:" + self.datasetname + "\n"
        print "self.dataset.type:" + self.dataset.type + "\n"

        # Load in the genotypes file *sigh* to make the markermap
        parser = genofile_parser.ConvertGenoFile(genofilelocation)
        parser.process_csv()
        snpinfo = []
        for marker in parser.markers:
          snpinfo.append(marker["name"]);
          snpinfo.append(marker["chr"]);
          snpinfo.append(marker["Mb"]);

        rnames = r_seq(1, len(parser.markers))
        # Create the snp aligner object out of the BXD genotypes
        snpaligner = ro.r.matrix(snpinfo, nrow=len(parser.markers), dimnames = r_list(rnames, r_c("SNP", "Chr", "Pos")), ncol = 3, byrow=True)

        # Create the phenotype aligner object using R
        phenoaligner = self.r_create_Pheno_aligner()

        print("Initialization of ePheWAS done !")

    def process_results(self, results):
        print("Processing ePheWAS output")
        template_vars = {}
        return(dict(template_vars))

