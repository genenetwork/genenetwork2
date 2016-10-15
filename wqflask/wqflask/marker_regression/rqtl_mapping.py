import rpy2.robjects as ro
import numpy as np

from base.webqtlConfig import TMPDIR
from utility import webqtlUtil
from utility.tools import locate, TEMPDIR

def run_rqtl_geno(vals, dataset, method, model, permCheck, num_perm, do_control, control_marker, manhattan_plot, pair_scan):
    geno_to_rqtl_function(dataset)

    ## Get pointers to some common R functions
    r_library     = ro.r["library"]                 # Map the library function
    r_c           = ro.r["c"]                       # Map the c function
    r_sum         = ro.r["sum"]                     # Map the sum function
    plot          = ro.r["plot"]                    # Map the plot function
    postscript    = ro.r["postscript"]              # Map the postscript function
    png           = ro.r["png"]                     # Map the png function
    dev_off       = ro.r["dev.off"]                 # Map the device off function

    print(r_library("qtl"))                         # Load R/qtl

    ## Get pointers to some R/qtl functions
    scanone         = ro.r["scanone"]               # Map the scanone function
    scantwo         = ro.r["scantwo"]               # Map the scantwo function
    calc_genoprob   = ro.r["calc.genoprob"]         # Map the calc.genoprob function
    read_cross      = ro.r["read.cross"]            # Map the read.cross function
    write_cross     = ro.r["write.cross"]           # Map the write.cross function
    GENOtoCSVR      = ro.r["GENOtoCSVR"]            # Map the local GENOtoCSVR function

    crossname = dataset.group.name
    genofilelocation  = locate(crossname + ".geno", "genotype")
    crossfilelocation = TMPDIR + crossname + ".cross"

    #print("Conversion of geno to cross at location:", genofilelocation, " to ", crossfilelocation)

    cross_object = GENOtoCSVR(genofilelocation, crossfilelocation)                                  # TODO: Add the SEX if that is available

    if manhattan_plot:
        cross_object = calc_genoprob(cross_object)
    else:
        cross_object = calc_genoprob(cross_object, step=1, stepwidth="max")

    cross_object = add_phenotype(cross_object, sanitize_rqtl_phenotype(vals))                 # Add the phenotype

    # for debug: write_cross(cross_object, "csvr", "test.csvr")

    # Scan for QTLs
    covar = create_covariates(control_marker, cross_object)                                                    # Create the additive covariate matrix

    if pair_scan:
        if do_control == "true":                                                # If sum(covar) > 0 we have a covariate matrix
            print("Using covariate"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", addcovar = covar, model=model, method=method, n_cluster = 16)
        else:
            print("No covariates"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", model=model, method=method, n_cluster = 16)

        #print("Pair scan results:", result_data_frame)

        pair_scan_filename = webqtlUtil.genRandStr("scantwo_") + ".png"
        png(file=TEMPDIR+pair_scan_filename)
        plot(result_data_frame)
        dev_off()

        return process_pair_scan_results(result_data_frame)
    else:
        if do_control == "true":
            print("Using covariate"); result_data_frame = scanone(cross_object, pheno = "the_pheno", addcovar = covar, model=model, method=method)
        else:
            print("No covariates"); result_data_frame = scanone(cross_object, pheno = "the_pheno", model=model, method=method)

        if num_perm > 0 and permCheck == "ON":                                                                   # Do permutation (if requested by user)
            if do_control == "true":
                perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", addcovar = covar, n_perm = num_perm, model=model, method=method)
            else:
                perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", n_perm = num_perm, model=model, method=method)

            perm_output, suggestive, significant = process_rqtl_perm_results(num_perm, perm_data_frame)          # Functions that sets the thresholds for the webinterface
            return perm_output, suggestive, significant, process_rqtl_results(result_data_frame)
        else:
            return process_rqtl_results(result_data_frame)

def geno_to_rqtl_function(dataset):        # TODO: Need to figure out why some genofiles have the wrong format and don't convert properly

    ro.r("""
       trim <- function( x ) { gsub("(^[[:space:]]+|[[:space:]]+$)", "", x) }

       getGenoCode <- function(header, name = 'unk'){
         mat = which(unlist(lapply(header,function(x){ length(grep(paste('@',name,sep=''), x)) })) == 1)
         return(trim(strsplit(header[mat],':')[[1]][2]))
       }

       GENOtoCSVR <- function(genotypes = '%s', out = 'cross.csvr', phenotype = NULL, sex = NULL, verbose = FALSE){
         header = readLines(genotypes, 40)                                                                                 # Assume a geno header is not longer than 40 lines
         toskip = which(unlist(lapply(header, function(x){ length(grep("Chr\t", x)) })) == 1)-1                            # Major hack to skip the geno headers

         genocodes <- c(getGenoCode(header, 'mat'), getGenoCode(header, 'het'), getGenoCode(header, 'pat'))                # Get the genotype codes
         type <- getGenoCode(header, 'type')
         genodata <- read.csv(genotypes, sep='\t', skip=toskip, header=TRUE, na.strings=getGenoCode(header,'unk'), colClasses='character', comment.char = '#')
         cat('Genodata:', toskip, " ", dim(genodata), genocodes, '\n')
         if(is.null(phenotype)) phenotype <- runif((ncol(genodata)-4))                                                     # If there isn't a phenotype, generate a random one
         if(is.null(sex)) sex <- rep('m', (ncol(genodata)-4))                                                              # If there isn't a sex phenotype, treat all as males
         outCSVR <- rbind(c('Pheno', '', '', phenotype),                                                                   # Phenotype
                          c('sex', '', '', sex),                                                                           # Sex phenotype for the mice
                          cbind(genodata[,c('Locus','Chr', 'cM')], genodata[, 5:ncol(genodata)]))                          # Genotypes
         write.table(outCSVR, file = out, row.names=FALSE, col.names=FALSE,quote=FALSE, sep=',')                           # Save it to a file
         require(qtl)
         cross = read.cross(file=out, 'csvr', genotypes=genocodes)                                                         # Load the created cross file using R/qtl read.cross
         if(type == 'riset') cross <- convert2riself(cross)                                                                # If its a RIL, convert to a RIL in R/qtl
         return(cross)
      }
    """ % (dataset.group.name + ".geno"))

def add_phenotype(cross, pheno_as_string):
    ro.globalenv["the_cross"] = cross
    ro.r('the_cross$pheno <- cbind(pull.pheno(the_cross), the_pheno = '+ pheno_as_string +')')
    return ro.r["the_cross"]

def create_covariates(control_marker, cross):
    ro.globalenv["the_cross"] = cross
    ro.r('genotypes <- pull.geno(the_cross)')                             # Get the genotype matrix
    userinputS = control_marker.replace(" ", "").split(",")                 # TODO: sanitize user input, Never Ever trust a user
    covariate_names = ', '.join('"{0}"'.format(w) for w in userinputS)
    #print("Marker names of selected covariates:", covariate_names)
    ro.r('covnames <- c(' + covariate_names + ')')
    ro.r('covInGeno <- which(covnames %in% colnames(genotypes))')
    ro.r('covnames <- covnames[covInGeno]')
    ro.r("cat('covnames (purged): ', covnames,'\n')")
    ro.r('covariates <- genotypes[,covnames]')                            # Get the covariate matrix by using the marker name as index to the genotype file
    #print("R/qtl matrix of covariates:", ro.r["covariates"])
    return ro.r["covariates"]

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

def process_pair_scan_results(result):
    pair_scan_results = []

    result = result[1]
    output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]
    #print("R/qtl scantwo output:", output)

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

def process_rqtl_results(result):        # TODO: how to make this a one liner and not copy the stuff in a loop
    qtl_results = []

    output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]
    #print("R/qtl scanone output:", output)

    for i, line in enumerate(result.iter_row()):
        marker = {}
        marker['name'] = result.rownames[i]
        marker['chr'] = output[i][0]
        marker['Mb'] = output[i][1]
        marker['lod_score'] = output[i][2]
        qtl_results.append(marker)

    return qtl_results

