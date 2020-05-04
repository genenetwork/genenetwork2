import rpy2.robjects as ro
import rpy2.robjects.numpy2ri as np2r
import numpy as np

from base.webqtlConfig import TMPDIR
from base.trait import GeneralTrait
from base.data_set import create_dataset
from utility import webqtlUtil
from utility.tools import locate, TEMPDIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

def run_rqtl_geno(vals, samples, dataset, method, model, permCheck, num_perm, perm_strata_list, do_control, control_marker, manhattan_plot, pair_scan, cofactors):
    ## Get pointers to some common R functions
    r_library     = ro.r["library"]                 # Map the library function
    r_c           = ro.r["c"]                       # Map the c function
    plot          = ro.r["plot"]                    # Map the plot function
    png           = ro.r["png"]                     # Map the png function
    dev_off       = ro.r["dev.off"]                 # Map the device off function

    print(r_library("qtl"))                         # Load R/qtl

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
    generate_cross_from_geno(dataset)
    GENOtoCSVR                 = ro.r["GENOtoCSVR"]            # Map the local GENOtoCSVR function
    crossfilelocation = TMPDIR + crossname + ".cross"
    if dataset.group.genofile:
        genofilelocation  = locate(dataset.group.genofile, "genotype")
    else:
        genofilelocation = locate(dataset.group.name + ".geno", "genotype")
    cross_object = GENOtoCSVR(genofilelocation, crossfilelocation)      # TODO: Add the SEX if that is available

    the_version = ro.r["packageVersion('qtl')"]
    logger.debug("THE R VERSION:", the_version)

    ro.r('save.image(file = "/home/zas1024/gn2-zach/tmp/HET3_cofactor_test2.RData")')

    if manhattan_plot:
        cross_object = calc_genoprob(cross_object)
    else:
        cross_object = calc_genoprob(cross_object, step=1, stepwidth="max")

    pheno_string = sanitize_rqtl_phenotype(vals)

    cross_object = add_phenotype(cross_object, pheno_string, "the_pheno")                 # Add the phenotype

    # Scan for QTLs
    marker_covars = create_marker_covariates(control_marker, cross_object)  # Create the additive covariate markers

    if cofactors != "":
        cross_object, trait_covars = add_cofactors(cross_object, dataset, cofactors, samples)                            # Create the covariates from selected traits
        ro.r('all_covars <- cbind(marker_covars, trait_covars)')
    else:
        ro.r('all_covars <- marker_covars')

    covars = ro.r['all_covars']

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
            the_scale = check_mapping_scale(genofilelocation)
            return perm_output, suggestive, significant, process_rqtl_results(result_data_frame, dataset.group.species), the_scale
        else:
            the_scale = check_mapping_scale(genofilelocation)
            return process_rqtl_results(result_data_frame, dataset.group.species), the_scale

def generate_cross_from_rdata(dataset):
    rdata_location  = locate(dataset.group.name + ".RData", "genotype/rdata")
    ro.r("""
       generate_cross_from_rdata <- function(filename = '%s') {
           load(file=filename)
           cross = cunique
           return(cross)
       }
    """ % (rdata_location))

def generate_cross_from_geno(dataset):        # TODO: Need to figure out why some genofiles have the wrong format and don't convert properly

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
            genocodes <- c('1','2','3','4')
         } else {
            genocodes <- c(getGenoCode(header, 'mat'), getGenoCode(header, 'het'), getGenoCode(header, 'pat'))                # Get the genotype codes
         }
         genodata <- read.csv(genotypes, sep='\t', skip=toskip, header=TRUE, na.strings=getGenoCode(header,'unk'), colClasses='character', comment.char = '#')
         cat('Genodata:', toskip, " ", dim(genodata), genocodes, '\n')
         if(is.null(phenotype)) phenotype <- runif((ncol(genodata)-4))                                                     # If there isn't a phenotype, generate a random one
         if(is.null(sex)) sex <- rep('m', (ncol(genodata)-4))                                                              # If there isn't a sex phenotype, treat all as males
         outCSVR <- rbind(c('Pheno', '', '', phenotype),                                                                   # Phenotype
                          c('sex', '', '', sex),                                                                           # Sex phenotype for the mice
                          cbind(genodata[,c('Locus','Chr', 'cM')], genodata[, 5:ncol(genodata)]))                          # Genotypes
         write.table(outCSVR, file = out, row.names=FALSE, col.names=FALSE,quote=FALSE, sep=',')                           # Save it to a file
         require(qtl)
         cross = read.cross(file=out, 'csvr', genotypes=genocodes, crosstype="4way", convertXdata=FALSE)                 # Load the created cross file using R/qtl read.cross
         #cross = read.cross(file=out, 'csvr', genotypes=genocodes)                                                         # Load the created cross file using R/qtl read.cross
         if(type == 'riset') cross <- convert2riself(cross)                                                                # If its a RIL, convert to a RIL in R/qtl
         return(cross)
      }
    """ % (dataset.group.genofile))

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

def add_phenotype(cross, pheno_as_string, col_name):
    ro.globalenv["the_cross"] = cross
    ro.r('the_cross$pheno <- cbind(pull.pheno(the_cross), ' + col_name + ' = '+ pheno_as_string +')')
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
        this_covar_data = []
        covar_as_string = "c("
        trait_name = covariate.split(":")[0]
        dataset_ob = create_dataset(covariate.split(":")[1])
        trait_ob = GeneralTrait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)

        this_dataset.group.get_samplelist()
        trait_samples = this_dataset.group.samplelist
        trait_sample_data = trait_ob.data
        for index, sample in enumerate(trait_samples):
            if sample in samples:
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
    userinputS = control_marker.replace(" ", "").split(",")               # TODO: sanitize user input, Never Ever trust a user
    covariate_names = ', '.join('"{0}"'.format(w) for w in userinputS)
    ro.r('covnames <- c(' + covariate_names + ')')
    ro.r('covInGeno <- which(covnames %in% colnames(genotypes))')
    ro.r('covnames <- covnames[covInGeno]')
    ro.r("cat('covnames (purged): ', covnames,'\n')")
    ro.r('marker_covars <- genotypes[,covnames]')                            # Get the covariate matrix by using the marker name as index to the genotype file

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

def check_mapping_scale(genofile_location):
    scale = "physic"
    with open(genofile_location, "r") as geno_fh:
        for line in geno_fh:
            if line[0] == "@" or line[0] == "#":

                if "@scale" in line:
                    scale = line.split(":")[1].strip()
                    break
                else:
                    continue
            else:
                break

    return scale