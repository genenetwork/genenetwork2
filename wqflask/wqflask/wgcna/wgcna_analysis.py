# WGCNA analysis for GN2
# Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>

from numpy import *
import scipy as sp                            # SciPy
import rpy2.robjects as ro                    # R Objects

from utility import helper_functions

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
r_sink          = ro.r["sink"]                # Map the sink function
r_file          = ro.r["file"]                # Map the file function
r_png           = ro.r["png"]                 # Map the png function for plotting
r_dev_off       = ro.r["dev.off"]             # Map the dev.off function

class WGCNA(object):
    def __init__(self):
        print("Initialization of WGCNA")
        log = r_file("/tmp/genenetwork_wcgna.log", open = "wt")
        #r_sink(log)                                  # Uncomment the r_sink() commands to log output from stdout/stderr to a file
        #r_sink(log, type = "message")
        r_library("WGCNA")                            # Load WGCNA - Should only be done once, since it is quite expensive
        r_options(stringsAsFactors = False)
        print("Initialization of WGCNA done, package loaded in R session")
        self.r_enableWGCNAThreads    = ro.r["enableWGCNAThreads"]        # Map the enableWGCNAThreads function
        self.r_pickSoftThreshold     = ro.r["pickSoftThreshold"]         # Map the pickSoftThreshold function
        self.r_blockwiseModules      = ro.r["blockwiseModules"]          # Map the blockwiseModules function
        self.r_labels2colors         = ro.r["labels2colors"]             # Map the labels2colors function
        self.r_plotDendroAndColors   = ro.r["plotDendroAndColors"]       # Map the plotDendroAndColors function
        print("Obtained pointers to WGCNA functions")

    def run_analysis(self, requestform):
        print("Starting WGCNA analysis on dataset")
        self.r_enableWGCNAThreads()                                      # Enable multi threading
        self.trait_db_list = [trait.strip() for trait in requestform['trait_list'].split(',')]
        print("Retrieved phenotype data from database", requestform['trait_list'])
        helper_functions.get_trait_db_obs(self, self.trait_db_list)
        self.results = {}
        for t in self.trait_list:
            strains = []
            for s in t[0].data:
                strains.append(s)
            self.results[t]  = strains

        print("Retrieved phenotype data from database")

    def process_results(self, results):
        print("Processing WGCNA output")
        template_vars = {}
        template_vars["result"] = self.results
        #r_sink(type = "message")                                   # This restores R output to the stdout/stderr
        #r_sink()                                                   # We should end the Rpy session more or less
        return(dict(template_vars))

