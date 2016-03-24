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
import itertools

from base import data_set
from base import trait as TRAIT

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
r_t             = ro.r["t"]                   # Map the t function
r_cat           = ro.r["cat"]                 # Map the cat function
r_paste         = ro.r["paste"]               # Map the paste function
r_unlist        = ro.r["unlist"]              # Map the unlist function
r_head          = ro.r["head"]                # Map the unlist function
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
r_save_image    = ro.r["save.image"]          # Map the save.image function
r_class         = ro.r["class"]               # Map the class function
r_save          = ro.r["save"]                # Map the save function
r_write_table   = ro.r["write.table"]         # Map the write.table function
r_read_table   = ro.r["read.table"]         # Map the read.table function
r_as_data_frame = ro.r["as.data.frame"]         # Map the write.table function
r_data_frame    = ro.r["data.frame"]         # Map the write.table function
r_as_numeric    = ro.r["as.numeric"]         # Map the write.table function

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
        self.r_CTLsignificant     = ro.r["CTLsignificant"]                 # Map the CTLsignificant function
        print("Obtained pointers to CTL functions")

    def run_analysis(self, requestform):
        print("Starting CTL analysis on dataset")
        self.trait_db_list = [trait.strip() for trait in requestform['trait_list'].split(',')]
        self.trait_db_list = [x for x in self.trait_db_list if x]

        print("strategy:", requestform.get("strategy"))
        strategy = requestform.get("strategy")

        print("nperm:", requestform.get("nperm"))
        nperm = int(requestform.get("nperm"))

        print("parametric:", requestform.get("parametric"))
        parametric = bool(requestform.get("parametric"))

        print("significance:", requestform.get("significance"))
        significance = float(requestform.get("significance"))

        # Get the name of the .geno file belonging to the first phenotype
        datasetname = self.trait_db_list[0].split(":")[1]
        dataset = data_set.create_dataset(datasetname)

        genofilelocation = locate(dataset.group.name + ".geno", "genotype")
        parser = genofile_parser.ConvertGenoFile(genofilelocation)
        parser.process_csv()

        # Create a genotype matrix
        individuals = parser.individuals
        markers = []
        markernames = []
        for marker in parser.markers:
          markernames.append(marker["name"])
          markers.append(marker["genotypes"])

        genotypes = list(itertools.chain(*markers))
        print(len(genotypes) / len(individuals), "==", len(parser.markers))

        rGeno = r_t(ro.r.matrix(r_unlist(genotypes), nrow=len(markernames), ncol=len(individuals), dimnames = r_list(markernames, individuals), byrow=True))

        # Create a phenotype matrix
        traits = []
        for trait in self.trait_db_list:
          print("retrieving data for", trait)
          if trait != "":
            ts = trait.split(':')
            gt = TRAIT.GeneralTrait(name = ts[0], dataset_name = ts[1])
            gt.retrieve_sample_data(individuals)
            for ind in individuals:
              if ind in gt.data.keys():
                traits.append(gt.data[ind].value)
              else:
                traits.append("-999")

        rPheno = r_t(ro.r.matrix(r_as_numeric(r_unlist(traits)), nrow=len(self.trait_db_list), ncol=len(individuals), dimnames = r_list(self.trait_db_list, individuals), byrow=True))

        # Use a data frame to store the objects
        rPheno = r_data_frame(rPheno)
        rGeno = r_data_frame(rGeno)

        # Debug: Print the genotype and phenotype files to disk
        #r_write_table(rGeno, "~/outputGN/geno.csv")
        #r_write_table(rPheno, "~/outputGN/pheno.csv")

        # Perform the CTL scan
        res = self.r_CTLscan(rGeno, rPheno, strategy = strategy, nperm = nperm, parametric = parametric, ncores = 6)

        # Get significant interactions
        significant = self.r_CTLsignificant(res, significance = significance)

        # Create an image for output
        self.results = {}
        self.results['imgurl'] = webqtlUtil.genRandStr("WGCNAoutput_") + ".png"
        self.results['imgloc'] = GENERATED_IMAGE_DIR + self.results['imgurl']
        self.results['ctlresult'] = significant
        self.results['requestform'] = requestform             # Store the user specified parameters for the output page

        # Create the lineplot
        r_png(self.results['imgloc'], width=1000, height=600)
        self.r_lineplot(res, significance = significance)
        r_dev_off()

        # Flush any output from R
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
        template_vars["results"] = self.results
        self.render_image(self.results)
        sys.stdout.flush()
        return(dict(template_vars))

