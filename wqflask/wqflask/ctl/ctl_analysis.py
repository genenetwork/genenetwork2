# CTL analysis for GN2
# Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>
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

from utility import helper_functions
from utility.tools import locate

from rpy2.robjects.packages import importr
utils = importr("utils")

## Get pointers to some common R functions
r_library       = ro.r["library"]             # Map the library function
r_options       = ro.r["options"]             # Map the options function
r_read_csv      = ro.r["read.csv"]            # Map the read.csv function
r_dim           = ro.r["dim"]                 # Map the dim function
r_c             = ro.r["c"]                   # Map the c function
r_cat           = ro.r["cat"]                 # Map the cat function
r_paste         = ro.r["paste"]               # Map the paste function
r_unlist        = ro.r["unlist"]              # Map the unlist function
r_unique        = ro.r["unique"]              # Map the unique function
r_length        = ro.r["length"]              # Map the length function
r_unlist        = ro.r["unlist"]              # Map the unlist function
r_list          = ro.r.list                   # Map the list function
r_matrix        = ro.r.matrix                 # Map the matrix function
r_seq           = ro.r["seq"]                 # Map the seq function
r_table         = ro.r["table"]               # Map the table function
r_names         = ro.r["names"]               # Map the names function
r_sink          = ro.r["sink"]                # Map the sink function
r_is_NA         = ro.r["is.na"]               # Map the is.na function
r_file          = ro.r["file"]                # Map the file function
r_png           = ro.r["png"]                 # Map the png function for plotting
r_dev_off       = ro.r["dev.off"]             # Map the dev.off function

class CTL(object):
    def __init__(self):
        print("Initialization of CTL")
        #log = r_file("/tmp/genenetwork_ctl.log", open = "wt")
        #r_sink(log)                                  # Uncomment the r_sink() commands to log output from stdout/stderr to a file
        #r_sink(log, type = "message")
        r_library("ctl")                                                  # Load CTL - Should only be done once, since it is quite expensive
        r_options(stringsAsFactors = False)
        print("Initialization of CTL done, package loaded in R session")
        self.r_CTLscan            = ro.r["CTLscan"]                        # Map the CTLscan function
        self.r_CTLsignificant     = ro.r["CTLsignificant"]                 # Map the CTLsignificant function
        self.r_lineplot           = ro.r["ctl.lineplot"]                   # Map the ctl.lineplot function
        self.r_CTLnetwork         = ro.r["CTLnetwork"]                     # Map the CTLnetwork function
        self.r_CTLprofiles        = ro.r["CTLprofiles"]                    # Map the CTLprofiles function
        print("Obtained pointers to CTL functions")

    def run_analysis(self, requestform):
        print("Starting CTL analysis on dataset")

        self.trait_db_list = [trait.strip() for trait in requestform['trait_list'].split(',')]
        print("Retrieved phenotype data from database", requestform['trait_list'])

        helper_functions.get_trait_db_obs(self, self.trait_db_list)

        self.input = {}           # self.input contains the phenotype values we need to send to R
        strains = []              # All the strains we have data for (contains duplicates)
        traits  = []              # All the traits we have data for (should not contain duplicates)
        genotypebasename = ""
        for trait in self.trait_list:
            traits.append(trait[0].name)
            if genotypebasename == "":
              genotypebasename = trait[1].group.name
            self.input[trait[0].name] = {}
            for strain in trait[0].data:
                strains.append(strain)
                self.input[trait[0].name][strain]  = trait[0].data[strain].value

        genofilelocation = locate(genotypebasename + ".geno", "genotype")
        parser = genofile_parser.ConvertGenoFile(genofilelocation)
        parser.process_csv()
        print(parser.markers)
        self.results = {}
        sys.stdout.flush()

    def render_image(self, results):
        print("pre-loading imgage results:", self.results['imgloc'])
        imgfile = open(self.results['imgloc'], 'rb')
        imgdata = imgfile.read()
        imgB64 = imgdata.encode("base64")
        bytesarray = array.array('B', imgB64)
        self.results['imgdata'] = bytesarray

    def process_results(self, results):
        print("Processing CTL output")
        template_vars = {}
        template_vars["input"] = self.input
        sys.stdout.flush()
        return(dict(template_vars))

