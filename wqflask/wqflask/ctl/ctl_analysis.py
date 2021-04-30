# CTL analysis for GN2
# Author / Maintainer: Danny Arends <Danny.Arends@gmail.com>
import sys
from numpy import *
import rpy2.robjects as ro                    # R Objects
import rpy2.rinterface as ri

import simplejson as json

from base.webqtlConfig import GENERATED_IMAGE_DIR
from utility import webqtlUtil                # Random number for the image
from utility import genofile_parser           # genofile_parser

import base64
import array
import csv
import itertools

from base import data_set
from base.trait import create_trait, retrieve_sample_data

from utility import helper_functions
from utility.tools import locate, GN2_BRANCH_URL

from rpy2.robjects.packages import importr

import utility.logger
logger = utility.logger.getLogger(__name__)

# Get pointers to some common R functions
r_library = ro.r["library"]             # Map the library function
r_options = ro.r["options"]             # Map the options function
r_t = ro.r["t"]                   # Map the t function
r_unlist = ro.r["unlist"]              # Map the unlist function
r_list = ro.r.list                   # Map the list function
r_png = ro.r["png"]                 # Map the png function for plotting
r_dev_off = ro.r["dev.off"]             # Map the dev.off function
r_write_table = ro.r["write.table"]         # Map the write.table function
r_data_frame = ro.r["data.frame"]         # Map the write.table function
r_as_numeric = ro.r["as.numeric"]         # Map the write.table function


class CTL:
    def __init__(self):
        logger.info("Initialization of CTL")
        #log = r_file("/tmp/genenetwork_ctl.log", open = "wt")
        # r_sink(log)                                                       # Uncomment the r_sink() commands to log output from stdout/stderr to a file
        #r_sink(log, type = "message")
        # Load CTL - Should only be done once, since it is quite expensive
        r_library("ctl")
        r_options(stringsAsFactors=False)
        logger.info("Initialization of CTL done, package loaded in R session")
        # Map the CTLscan function
        self.r_CTLscan = ro.r["CTLscan"]
        # Map the CTLsignificant function
        self.r_CTLsignificant = ro.r["CTLsignificant"]
        # Map the ctl.lineplot function
        self.r_lineplot = ro.r["ctl.lineplot"]
        # Map the CTLsignificant function
        self.r_plotCTLobject = ro.r["plot.CTLobject"]
        self.nodes_list = []
        self.edges_list = []
        logger.info("Obtained pointers to CTL functions")

        self.gn2_url = GN2_BRANCH_URL

    def addNode(self, gt):
        node_dict = {'data': {'id': str(gt.name) + ":" + str(gt.dataset.name),
                                'sid': str(gt.name),
                                'dataset': str(gt.dataset.name),
                                'label': gt.name,
                                'symbol': gt.symbol,
                                'geneid': gt.geneid,
                                'omim': gt.omim}}
        self.nodes_list.append(node_dict)

    def addEdge(self, gtS, gtT, significant, x):
        edge_data = {'id': str(gtS.symbol) + '_' + significant[1][x] + '_' + str(gtT.symbol),
                     'source': str(gtS.name) + ":" + str(gtS.dataset.name),
                     'target': str(gtT.name) + ":" + str(gtT.dataset.name),
                     'lod': significant[3][x],
                     'color': "#ff0000",
                     'width': significant[3][x]}
        edge_dict = {'data': edge_data}
        self.edges_list.append(edge_dict)

    def run_analysis(self, requestform):
        logger.info("Starting CTL analysis on dataset")
        self.trait_db_list = [trait.strip()
                                          for trait in requestform['trait_list'].split(',')]
        self.trait_db_list = [x for x in self.trait_db_list if x]

        logger.debug("strategy:", requestform.get("strategy"))
        strategy = requestform.get("strategy")

        logger.debug("nperm:", requestform.get("nperm"))
        nperm = int(requestform.get("nperm"))

        logger.debug("parametric:", requestform.get("parametric"))
        parametric = bool(requestform.get("parametric"))

        logger.debug("significance:", requestform.get("significance"))
        significance = float(requestform.get("significance"))

        # Get the name of the .geno file belonging to the first phenotype
        datasetname = self.trait_db_list[0].split(":")[1]
        dataset = data_set.create_dataset(datasetname)

        genofilelocation = locate(dataset.group.name + ".geno", "genotype")
        parser = genofile_parser.ConvertGenoFile(genofilelocation)
        parser.process_csv()
        logger.debug("dataset group: ", dataset.group)
        # Create a genotype matrix
        individuals = parser.individuals
        markers = []
        markernames = []
        for marker in parser.markers:
            markernames.append(marker["name"])
            markers.append(marker["genotypes"])

        genotypes = list(itertools.chain(*markers))
        logger.debug(len(genotypes) / len(individuals),
                     "==", len(parser.markers))

        rGeno = r_t(ro.r.matrix(r_unlist(genotypes), nrow=len(markernames), ncol=len(
            individuals), dimnames=r_list(markernames, individuals), byrow=True))

        # Create a phenotype matrix
        traits = []
        for trait in self.trait_db_list:
            logger.debug("retrieving data for", trait)
            if trait != "":
                ts = trait.split(':')
                gt = create_trait(name=ts[0], dataset_name=ts[1])
                gt = retrieve_sample_data(gt, dataset, individuals)
                for ind in individuals:
                    if ind in list(gt.data.keys()):
                        traits.append(gt.data[ind].value)
                    else:
                        traits.append("-999")

        rPheno = r_t(ro.r.matrix(r_as_numeric(r_unlist(traits)), nrow=len(self.trait_db_list), ncol=len(
            individuals), dimnames=r_list(self.trait_db_list, individuals), byrow=True))

        logger.debug(rPheno)

        # Use a data frame to store the objects
        rPheno = r_data_frame(rPheno, check_names=False)
        rGeno = r_data_frame(rGeno, check_names=False)

        # Debug: Print the genotype and phenotype files to disk
        #r_write_table(rGeno, "~/outputGN/geno.csv")
        #r_write_table(rPheno, "~/outputGN/pheno.csv")

        # Perform the CTL scan
        res = self.r_CTLscan(rGeno, rPheno, strategy=strategy,
                             nperm=nperm, parametric = parametric, nthreads=6)

        # Get significant interactions
        significant = self.r_CTLsignificant(res, significance=significance)

        # Create an image for output
        self.results = {}
        self.results['imgurl1'] = webqtlUtil.genRandStr("CTLline_") + ".png"
        self.results['imgloc1'] = GENERATED_IMAGE_DIR + self.results['imgurl1']

        self.results['ctlresult'] = significant
        # Store the user specified parameters for the output page
        self.results['requestform'] = requestform

        # Create the lineplot
        r_png(self.results['imgloc1'], width=1000,
              height=600, type='cairo-png')
        self.r_lineplot(res, significance=significance)
        r_dev_off()

        # We start from 2, since R starts from 1 :)
        n = 2
        for trait in self.trait_db_list:
            # Create the QTL like CTL plots
            self.results['imgurl' + \
                str(n)] = webqtlUtil.genRandStr("CTL_") + ".png"
            self.results['imgloc' + str(n)] = GENERATED_IMAGE_DIR + \
                                        self.results['imgurl' + str(n)]
            r_png(self.results['imgloc' + str(n)],
                  width=1000, height=600, type='cairo-png')
            self.r_plotCTLobject(
                res, (n - 1), significance=significance, main='Phenotype ' + trait)
            r_dev_off()
            n = n + 1

        # Flush any output from R
        sys.stdout.flush()

        # Create the interactive graph for cytoscape visualization (Nodes and Edges)
        if not isinstance(significant, ri.RNULLType):
            for x in range(len(significant[0])):
                logger.debug(significant[0][x], significant[1]
                             [x], significant[2][x])     # Debug to console
                # Source
                tsS = significant[0][x].split(':')
                # Target
                tsT = significant[2][x].split(':')
                # Retrieve Source info from the DB
                gtS = create_trait(name=tsS[0], dataset_name=tsS[1])
                # Retrieve Target info from the DB
                gtT = create_trait(name=tsT[0], dataset_name=tsT[1])
                self.addNode(gtS)
                self.addNode(gtT)
                self.addEdge(gtS, gtT, significant, x)

                # Update the trait name for the displayed table
                significant[0][x] = "{} ({})".format(gtS.symbol, gtS.name)
                # Update the trait name for the displayed table
                significant[2][x] = "{} ({})".format(gtT.symbol, gtT.name)

        self.elements = json.dumps(self.nodes_list + self.edges_list)

    def loadImage(self, path, name):
        imgfile = open(self.results[path], 'rb')
        imgdata = imgfile.read()
        imgB64 = base64.b64encode(imgdata)
        bytesarray = array.array('B', imgB64)
        self.results[name] = bytesarray

    def render_image(self, results):
        self.loadImage("imgloc1", "imgdata1")
        n = 2
        for trait in self.trait_db_list:
            self.loadImage("imgloc" + str(n), "imgdata" + str(n))
            n = n + 1

    def process_results(self, results):
        logger.info("Processing CTL output")
        template_vars = {}
        template_vars["results"] = self.results
        template_vars["elements"] = self.elements
        self.render_image(self.results)
        sys.stdout.flush()
        return(dict(template_vars))
