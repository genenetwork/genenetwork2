import rpy2.robjects as ro
import rpy2.robjects.numpy2ri as np2r
import numpy as np
import json

from flask import g

from base.webqtlConfig import TMPDIR
from base.trait import create_trait
from base.data_set import create_dataset
from utility import webqtlUtil
from utility.tools import locate, TEMPDIR
from flask import g

import utility.logger
logger = utility.logger.getLogger(__name__ )

# Get a trait's type (numeric, categorical, etc) from the DB
def get_trait_data_type(trait_db_string):
    logger.info("get_trait_data_type");
    the_query = "SELECT value FROM TraitMetadata WHERE type='trait_data_type'"
    logger.info("the_query done");
    results_json = g.db.execute(the_query).fetchone()
    logger.info("the_query executed");
    results_ob = json.loads(results_json[0])
    logger.info("json results loaded");
    if trait_db_string in results_ob:
        logger.info("found");
        return results_ob[trait_db_string]
    else:
        logger.info("not found");
        return "numeric"


# Run qtl mapping using R/qtl
def run_rqtl_geno(vals, samples, dataset, mapping_scale, method, model, permCheck, num_perm, perm_strata_list, do_control, control_marker, manhattan_plot, pair_scan, cofactors):
    logger.info("Start run_rqtl_geno");
    ## Get pointers to some common R functions
    r_library     = ro.r["library"]                 # Map the library function
    r_c           = ro.r["c"]                       # Map the c function
    plot          = ro.r["plot"]                    # Map the plot function
    png           = ro.r["png"]                     # Map the png function
    dev_off       = ro.r["dev.off"]                 # Map the device off function

    print((r_library("qtl")))                         # Load R/qtl

    logger.info("QTL library loaded");

    ## Get pointers to some R/qtl functions
    scanone                    = ro.r["scanone"]               # Map the scanone function
    scantwo                    = ro.r["scantwo"]               # Map the scantwo function
    calc_genoprob              = ro.r["calc.genoprob"]         # Map the calc.genoprob function

    crossname = dataset.group.name
    #try:
    #    generate_cross_from_rdata(dataset)
    #    read_cross_from_rdata      = ro.r["generate_cross_from_rdata"] # Map the local read_cross_from_rdata function
    #    genofilelocation  = locate(crossname + ".RData", "genotype/rdata")
    #    cross_object = read_cross_from_rdata(genofilelocation)  # Map the local GENOtoCSVR function
    #except:

    if mapping_scale == "morgan":
        scale_units = "cM"
    else:
        scale_units = "Mb"

    generate_cross_from_geno(dataset, scale_units)
    GENOtoCSVR                 = ro.r["GENOtoCSVR"]            # Map the local GENOtoCSVR function
    crossfilelocation = TMPDIR + crossname + ".cross"
    if dataset.group.genofile:
        genofilelocation  = locate(dataset.group.genofile, "genotype")
    else:
        genofilelocation = locate(dataset.group.name + ".geno", "genotype")
    logger.info("Going to create a cross from geno");
    cross_object = GENOtoCSVR(genofilelocation, crossfilelocation)      # TODO: Add the SEX if that is available
    logger.info("before calc_genoprob");
    if manhattan_plot:
        cross_object = calc_genoprob(cross_object)
    else:
        cross_object = calc_genoprob(cross_object, step=5, stepwidth="max")
    logger.info("after calc_genoprob");
    pheno_string = sanitize_rqtl_phenotype(vals)
    logger.info("phenostring done");
    names_string = sanitize_rqtl_names(samples)
    logger.info("sanitized pheno and names");
    cross_object = add_phenotype(cross_object, pheno_string, "the_pheno")                 # Add the phenotype
    cross_object = add_names(cross_object, names_string, "the_names")                 # Add the phenotype
    logger.info("Added pheno and names");
    marker_covars = create_marker_covariates(control_marker, cross_object)  # Create the additive covariate markers
    logger.info("Marker covars done");
    if cofactors != "":
        logger.info("Cofactors: " + cofactors);
        cross_object, trait_covars = add_cofactors(cross_object, dataset, cofactors, samples)  # Create the covariates from selected traits
        ro.r('all_covars <- cbind(marker_covars, trait_covars)')
    else:
        ro.r('all_covars <- marker_covars')
    covars = ro.r['all_covars']
    #DEBUG to save the session object to file
    if pair_scan:
        if do_control == "true":
            logger.info("Using covariate"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", addcovar = covars, model=model, method=method, n_cluster = 16)
        else:
            logger.info("No covariates"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", model=model, method=method, n_cluster = 16)

        pair_scan_filename = webqtlUtil.genRandStr("scantwo_") + ".png"
        png(file=TEMPDIR+pair_scan_filename)
        plot(result_data_frame)
        dev_off()

        return process_pair_scan_results(result_data_frame)
    else:
        if do_control == "true" or cofactors != "":
            logger.info("Using covariate"); result_data_frame = scanone(cross_object, pheno = "the_pheno", addcovar = covars, model=model, method=method)
            ro.r('save.image(file = "/home/zas1024/gn2-zach/itp_cofactor_test.RData")')
        else:
            logger.info("No covariates"); result_data_frame = scanone(cross_object, pheno = "the_pheno", model=model, method=method)

        if num_perm > 0 and permCheck == "ON":                                                                   # Do permutation (if requested by user)
            if len(perm_strata_list) > 0: #ZS: The strata list would only be populated if "Stratified" was checked on before mapping
                cross_object, strata_ob = add_perm_strata(cross_object, perm_strata_list)
                if do_control == "true" or cofactors != "":
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", addcovar = covars, n_perm = int(num_perm), perm_strata = strata_ob, model=model, method=method)
                else:
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", n_perm = num_perm, perm_strata = strata_ob, model=model, method=method)
            else:
                if do_control == "true" or cofactors != "":
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", addcovar = covars, n_perm = int(num_perm), model=model, method=method)
                else:
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", n_perm = num_perm, model=model, method=method)

            perm_output, suggestive, significant = process_rqtl_perm_results(num_perm, perm_data_frame)          # Functions that sets the thresholds for the webinterface
            return perm_output, suggestive, significant, process_rqtl_results(result_data_frame, dataset.group.species)
        else:
            return process_rqtl_results(result_data_frame, dataset.group.species)

def generate_cross_from_rdata(dataset):
    rdata_location  = locate(dataset.group.name + ".RData", "genotype/rdata")
    ro.r("""
       generate_cross_from_rdata <- function(filename = '%s') {
           load(file=filename)
           cross = cunique
           return(cross)
       }
    """ % (rdata_location))

def generate_cross_from_geno(dataset, scale_units):        # TODO: Need to figure out why some genofiles have the wrong format and don't convert properly

    ro.r("""
       trim <- function( x ) { gsub("(^[[:space:]]+|[[:space:]]+$)", "", x) }
       getGenoCode <- function(header, name = 'unk'){
         mat = which(unlist(lapply(header,function(x){ length(grep(paste('@',name,sep=''), x)) })) == 1)
         return(trim(strsplit(header[mat],':')[[1]][2]))
       }
       GENOtoCSVR <- function(genotypes = '%s', out = 'cross.csvr', phenotype = NULL, sex = NULL, verbose = FALSE){
         header = readLines(genotypes, 40)                                                                                 # Assume a geno header is not longer than 40 lines
         toskip = which(unlist(lapply(header, function(x){ length(grep("Chr\t", x)) })) == 1)-1                            # Major hack to skip the geno headers
         type <- getGenoCode(header, 'type')
         if(type == '4-way'){
            genocodes <- NULL
         } else {
            genocodes <- c(getGenoCode(header, 'mat'), getGenoCode(header, 'het'), getGenoCode(header, 'pat'))             # Get the genotype codes
         }
         genodata <- read.csv(genotypes, sep='\t', skip=toskip, header=TRUE, na.strings=getGenoCode(header,'unk'), colClasses='character', comment.char = '#')
         cat('Genodata:', toskip, " ", dim(genodata), genocodes, '\n')
         if(is.null(phenotype)) phenotype <- runif((ncol(genodata)-4))                                                     # If there isn't a phenotype, generate a random one
         if(is.null(sex)) sex <- rep('m', (ncol(genodata)-4))                                                              # If there isn't a sex phenotype, treat all as males
         outCSVR <- rbind(c('Pheno', '', '', phenotype),                                                                   # Phenotype
                          c('sex', '', '', sex),                                                                           # Sex phenotype for the mice
                          cbind(genodata[,c('Locus','Chr', '%s')], genodata[, 5:ncol(genodata)]))                          # Genotypes
         write.table(outCSVR, file = out, row.names=FALSE, col.names=FALSE,quote=FALSE, sep=',')                           # Save it to a file
         require(qtl)
         if(type == '4-way'){
           cat('Loading in as 4-WAY\n')
           cross = read.cross(file=out, 'csvr', genotypes=NULL, crosstype="4way")                                         # Load the created cross file using R/qtl read.cross
         }else if(type == 'f2'){
           cat('Loading in as F2\n')
           cross = read.cross(file=out, 'csvr', genotypes=genocodes, crosstype="f2")                                       # Load the created cross file using R/qtl read.cross
         }else{
           cat('Loading in as normal\n')
           cross = read.cross(file=out, 'csvr', genotypes=genocodes)                                                       # Load the created cross file using R/qtl read.cross
         }
         if(type == 'riset'){
           cat('Converting to RISELF\n')
           cross <- convert2riself(cross)                                                                # If its a RIL, convert to a RIL in R/qtl
         }
         return(cross)
      }
    """ % (dataset.group.genofile, scale_units))

def add_perm_strata(cross, perm_strata):
    col_string = 'c("the_strata")'
    perm_strata_string = "c("
    for item in perm_strata:
        perm_strata_string += str(item) + ","

    perm_strata_string = perm_strata_string[:-1] + ")"

    cross = add_phenotype(cross, perm_strata_string, "the_strata")

    strata_ob = pull_var("perm_strata", cross, col_string)

    return cross, strata_ob

def sanitize_rqtl_phenotype(vals):
    pheno_as_string = "c("
    for i, val in enumerate(vals):
        if val == "x":
            if i < (len(vals) - 1):
                pheno_as_string +=  "NA,"
            else:
                pheno_as_string += "NA"
        else:
            if i < (len(vals) - 1):
                pheno_as_string += str(val) + ","
            else:
                pheno_as_string += str(val)
    pheno_as_string += ")"

    return pheno_as_string

def sanitize_rqtl_names(vals):
    pheno_as_string = "c("
    for i, val in enumerate(vals):
        if val == "x":
            if i < (len(vals) - 1):
                pheno_as_string +=  "NA,"
            else:
                pheno_as_string += "NA"
        else:
            if i < (len(vals) - 1):
                pheno_as_string += "'" + str(val) + "',"
            else:
                pheno_as_string += "'" + str(val) + "'"
    pheno_as_string += ")"

    return pheno_as_string

def add_phenotype(cross, pheno_as_string, col_name):
    ro.globalenv["the_cross"] = cross
    ro.r('pheno <- data.frame(pull.pheno(the_cross))')
    ro.r('the_cross$pheno <- cbind(pheno, ' + col_name + ' = as.numeric('+ pheno_as_string +'))')
    return ro.r["the_cross"]

def add_categorical_covar(cross, covar_as_string, i):
    ro.globalenv["the_cross"] = cross
    logger.info("cross set"); 
    ro.r('covar <- as.factor(' + covar_as_string + ')')
    logger.info("covar set"); 
    ro.r('newcovar <- model.matrix(~covar-1)')
    logger.info("model.matrix finished");
    ro.r('cat("new covar columns", ncol(newcovar), "\n")')
    nCol = ro.r('ncol(newcovar)')
    logger.info("ncol covar done: " + str(nCol[0]));
    ro.r('pheno <- data.frame(pull.pheno(the_cross))')
    logger.info("pheno pulled from cross");
    nCol = int(nCol[0])
    logger.info("nCol python int:" + str(nCol));
    col_names = []
    #logger.info("loop")
    for x in range(1, (nCol+1)):
      #logger.info("loop" + str(x));
      col_name = "covar_" + str(i) + "_" + str(x)
      #logger.info("col_name" + col_name);
      ro.r('the_cross$pheno <- cbind(pheno, ' + col_name + ' = newcovar[,' + str(x) + '])')
      col_names.append(col_name)
      #logger.info("loop" + str(x) + "done"); 

    logger.info("returning from add_categorical_covar");
    return ro.r["the_cross"], col_names


def add_names(cross, names_as_string, col_name):
    ro.globalenv["the_cross"] = cross
    ro.r('pheno <- data.frame(pull.pheno(the_cross))')
    ro.r('the_cross$pheno <- cbind(pheno, ' + col_name + ' = '+ names_as_string +')')
    return ro.r["the_cross"]

def pull_var(var_name, cross, var_string):
    ro.globalenv["the_cross"] = cross
    ro.r(var_name +' <- pull.pheno(the_cross, ' + var_string + ')')

    return ro.r[var_name]

def add_cofactors(cross, this_dataset, covariates, samples):
    ro.numpy2ri.activate()

    covariate_list = covariates.split(",")
    covar_name_string = "c("
    for i, covariate in enumerate(covariate_list):
        logger.info("Covariate: " + covariate);
        this_covar_data = []
        covar_as_string = "c("
        trait_name = covariate.split(":")[0]
        dataset_ob = create_dataset(covariate.split(":")[1])
        trait_ob = create_trait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)

        this_dataset.group.get_samplelist()
        trait_samples = this_dataset.group.samplelist
        trait_sample_data = trait_ob.data
        for index, sample in enumerate(samples):
            if sample in trait_samples:
                if sample in trait_sample_data:
                    sample_value = trait_sample_data[sample].value
                    this_covar_data.append(sample_value)
                else:
                    this_covar_data.append("NA")

        for j, item in enumerate(this_covar_data):
            if j < (len(this_covar_data) - 1):
                covar_as_string += str(item) + ","
            else:
                covar_as_string += str(item)

        covar_as_string += ")"

        datatype = get_trait_data_type(covariate)
        logger.info("Covariate: " + covariate + " is of type: " + datatype);
        if(datatype == "categorical"): # Cat variable
            logger.info("call of add_categorical_covar");
            cross, col_names = add_categorical_covar(cross, covar_as_string, i) # Expand and add it to the cross
            logger.info("add_categorical_covar returned");
            for z, col_name in enumerate(col_names): # Go through the additional covar names
                if i < (len(covariate_list) - 1):
                    covar_name_string += '"' + col_name + '", '
                else:
                    if(z < (len(col_names) -1)):
                        covar_name_string += '"' + col_name + '", '
                    else:
                        covar_name_string += '"' + col_name + '"'
        else:
            col_name = "covar_" + str(i)
            cross = add_phenotype(cross, covar_as_string, col_name)
            if i < (len(covariate_list) - 1):
                covar_name_string += '"' + col_name + '", '
            else:
                covar_name_string += '"' + col_name + '"'

    covar_name_string += ")"
    covars_ob = pull_var("trait_covars", cross, covar_name_string)
    return cross, covars_ob

def create_marker_covariates(control_marker, cross):
    ro.globalenv["the_cross"] = cross
    ro.r('genotypes <- pull.geno(the_cross)')                             # Get the genotype matrix
    userinput_sanitized = control_marker.replace(" ", "").split(",")               # TODO: sanitize user input, Never Ever trust a user
    logger.debug(userinput_sanitized)
    if len(userinput_sanitized) > 0:
        covariate_names = ', '.join('"{0}"'.format(w) for w in userinput_sanitized)
        ro.r('covnames <- c(' + covariate_names + ')')
    else:
        ro.r('covnames <- c()')
    ro.r('covInGeno <- which(covnames %in% colnames(genotypes))')
    ro.r('covnames <- covnames[covInGeno]')
    ro.r("cat('covnames (purged): ', covnames,'\n')")
    ro.r('marker_covars <- genotypes[,covnames]')                            # Get the covariate matrix by using the marker name as index to the genotype file
    # TODO: Create a design matrix from the marker covars for the markers in case of an F2, 4way, etc
    return ro.r["marker_covars"]

def process_pair_scan_results(result):
    pair_scan_results = []

    result = result[1]
    output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]

    for i, line in enumerate(result.iter_row()):
        marker = {}
        marker['name'] = result.rownames[i]
        marker['chr1'] = output[i][0]
        marker['Mb'] = output[i][1]
        marker['chr2'] = int(output[i][2])
        pair_scan_results.append(marker)

    return pair_scan_results

def process_rqtl_perm_results(num_perm, results):
    perm_vals = []
    for line in str(results).split("\n")[1:(num_perm+1)]:
        #print("R/qtl permutation line:", line.split())
        perm_vals.append(float(line.split()[1]))

    perm_output = perm_vals
    suggestive = np.percentile(np.array(perm_vals), 67)
    significant = np.percentile(np.array(perm_vals), 95)

    return perm_output, suggestive, significant

def process_rqtl_results(result, species_name):        # TODO: how to make this a one liner and not copy the stuff in a loop
    qtl_results = []
    output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]

    for i, line in enumerate(result.iter_row()):
        marker = {}
        marker['name'] = result.rownames[i]
        if species_name == "mouse" and output[i][0] == 20: #ZS: This is awkward, but I'm not sure how to change the 20s to Xs in the RData file
            marker['chr'] = "X"
        else:
            marker['chr'] = output[i][0]
        marker['cM'] = output[i][1]
        marker['Mb'] = output[i][1]
        marker['lod_score'] = output[i][2]
        qtl_results.append(marker)

    return qtl_results