"""
WGCNA analysis for GN2

Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>
"""
import base64
import sys
import rpy2.robjects as ro                    # R Objects
import rpy2.rinterface as ri

from array import array as arr
from numpy import *
from base.webqtlConfig import GENERATED_IMAGE_DIR
from rpy2.robjects.packages import importr

from utility import webqtlUtil                # Random number for the image
from utility import helper_functions

utils = importr("utils")

# Get pointers to some common R functions
r_library = ro.r["library"]    # Map the library function
r_options = ro.r["options"]    # Map the options function
r_read_csv = ro.r["read.csv"]  # Map the read.csv function
r_dim = ro.r["dim"]            # Map the dim function
r_c = ro.r["c"]                # Map the c function
r_cat = ro.r["cat"]            # Map the cat function
r_paste = ro.r["paste"]        # Map the paste function
r_unlist = ro.r["unlist"]      # Map the unlist function
r_unique = ro.r["unique"]      # Map the unique function
r_length = ro.r["length"]      # Map the length function
r_unlist = ro.r["unlist"]      # Map the unlist function
r_list = ro.r.list             # Map the list function
r_matrix = ro.r.matrix         # Map the matrix function
r_seq = ro.r["seq"]            # Map the seq function
r_table = ro.r["table"]        # Map the table function
r_names = ro.r["names"]        # Map the names function
r_sink = ro.r["sink"]          # Map the sink function
r_is_NA = ro.r["is.na"]        # Map the is.na function
r_file = ro.r["file"]          # Map the file function
r_png = ro.r["png"]            # Map the png function for plotting
r_dev_off = ro.r["dev.off"]    # Map the dev.off function


class WGCNA:
    def __init__(self):
        # To log output from stdout/stderr to a file add `r_sink(log)`
        print("Initialization of WGCNA")

        # Load WGCNA - Should only be done once, since it is quite expensive
        r_library("WGCNA")
        r_options(stringsAsFactors=False)
        print("Initialization of WGCNA done, package loaded in R session")
        # Map the enableWGCNAThreads function
        self.r_enableWGCNAThreads = ro.r["enableWGCNAThreads"]
        # Map the pickSoftThreshold function
        self.r_pickSoftThreshold = ro.r["pickSoftThreshold"]
        # Map the blockwiseModules function
        self.r_blockwiseModules = ro.r["blockwiseModules"]
        # Map the labels2colors function
        self.r_labels2colors = ro.r["labels2colors"]
        # Map the plotDendroAndColors function
        self.r_plotDendroAndColors = ro.r["plotDendroAndColors"]
        print("Obtained pointers to WGCNA functions")

    def run_analysis(self, requestform):
        print("Starting WGCNA analysis on dataset")
        # Enable multi threading
        self.r_enableWGCNAThreads()
        self.trait_db_list = [trait.strip()
                              for trait in requestform['trait_list'].split(',')]
        print(("Retrieved phenotype data from database",
               requestform['trait_list']))
        helper_functions.get_trait_db_obs(self, self.trait_db_list)

        # self.input contains the phenotype values we need to send to R
        self.input = {}
        # All the strains we have data for (contains duplicates)
        strains = []
        # All the traits we have data for (should not contain duplicates)
        traits = []
        for trait in self.trait_list:
            traits.append(trait[0].name)
            self.input[trait[0].name] = {}
            for strain in trait[0].data:
                strains.append(strain)
                self.input[trait[0].name][strain] = trait[0].data[strain].value

        # Transfer the load data from python to R
        # Unique strains in R vector
        uStrainsR = r_unique(ro.Vector(strains))
        uTraitsR = r_unique(ro.Vector(traits))      # Unique traits in R vector

        r_cat("The number of unique strains:", r_length(uStrainsR), "\n")
        r_cat("The number of unique traits:", r_length(uTraitsR), "\n")

        # rM is the datamatrix holding all the data in
        # R /rows = strains columns = traits
        rM = ro.r.matrix(ri.NA_Real, nrow=r_length(uStrainsR), ncol=r_length(
            uTraitsR), dimnames=r_list(uStrainsR, uTraitsR))
        for t in uTraitsR:
            # R uses vectors every single element is a vector
            trait = t[0]
            for s in uStrainsR:
                # R uses vectors every single element is a vector
                strain = s[0]
                rM.rx[strain, trait] = self.input[trait].get(
                    strain)  # Update the matrix location
                sys.stdout.flush()

        self.results = {}
        # Number of phenotypes/traits
        self.results['nphe'] = r_length(uTraitsR)[0]
        self.results['nstr'] = r_length(
            uStrainsR)[0]         # Number of strains
        self.results['phenotypes'] = uTraitsR                 # Traits used
        # Strains used in the analysis
        self.results['strains'] = uStrainsR
        # Store the user specified parameters for the output page
        self.results['requestform'] = requestform

        # Calculate soft threshold if the user specified the
        # SoftThreshold variable
        if requestform.get('SoftThresholds') is not None:
            powers = [int(threshold.strip())
                      for threshold in requestform['SoftThresholds'].rstrip().split(",")]
            rpow = r_unlist(r_c(powers))
            print(("SoftThresholds: {} == {}".format(powers, rpow)))
            self.sft = self.r_pickSoftThreshold(
                rM, powerVector=rpow, verbose=5)

            print(("PowerEstimate: {}".format(self.sft[0])))
            self.results['PowerEstimate'] = self.sft[0]
            if self.sft[0][0] is ri.NA_Integer:
                print("No power is suitable for the analysis, just use 1")
                # No power could be estimated
                self.results['Power'] = 1
            else:
                # Use the estimated power
                self.results['Power'] = self.sft[0][0]
        else:
            # The user clicked a button, so no soft threshold selection
            # Use the power value the user gives
            self.results['Power'] = requestform.get('Power')

        # Create the block wise modules using WGCNA
        network = self.r_blockwiseModules(
            rM,
            power=self.results['Power'],
            TOMType=requestform['TOMtype'],
            minModuleSize=requestform['MinModuleSize'],
            verbose=3)

        # Save the network for the GUI
        self.results['network'] = network

        # How many modules and how many gene per module ?
        print(("WGCNA found {} modules".format(r_table(network[1]))))
        self.results['nmod'] = r_length(r_table(network[1]))[0]

        # The iconic WCGNA plot of the modules in the hanging tree
        self.results['imgurl'] = webqtlUtil.genRandStr("WGCNAoutput_") + ".png"
        self.results['imgloc'] = GENERATED_IMAGE_DIR + self.results['imgurl']
        r_png(self.results['imgloc'], width=1000, height=600, type='cairo-png')
        mergedColors = self.r_labels2colors(network[1])
        self.r_plotDendroAndColors(network[5][0], mergedColors,
                                   "Module colors", dendroLabels=False,
                                   hang=0.03, addGuide=True, guideHang=0.05)
        r_dev_off()
        sys.stdout.flush()

    def render_image(self, results):
        print(("pre-loading imgage results:", self.results['imgloc']))
        imgfile = open(self.results['imgloc'], 'rb')
        imgdata = imgfile.read()
        imgB64 = base64.b64encode(imgdata)
        bytesarray = arr('B', imgB64)
        self.results['imgdata'] = bytesarray

    def process_results(self, results):
        print("Processing WGCNA output")
        template_vars = {}
        template_vars["input"] = self.input
        # Results from the soft threshold analysis
        template_vars["powers"] = self.sft[1:]
        template_vars["results"] = self.results
        self.render_image(results)
        sys.stdout.flush()
        return(dict(template_vars))
