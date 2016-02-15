from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import math
import sys
import datetime
import os
import collections
import uuid

import rpy2.robjects as ro
import numpy as np
from scipy import linalg

import cPickle as pickle

import simplejson as json

from redis import Redis
Redis = Redis()

from flask import Flask, g

from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from utility import webqtlUtil
#from wqflask.marker_regression import qtl_reaper_mapping
#from wqflask.marker_regression import plink_mapping
from wqflask.marker_regression import gemma_mapping
#from wqflask.marker_regression import rqtl_mapping
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data
from utility.benchmark import Bench
from utility.tools import pylmm_command, plink_command

PYLMM_PATH,PYLMM_COMMAND = pylmm_command()
PLINK_PATH,PLINK_COMMAND = plink_command()

class MarkerRegression(object):

    def __init__(self, start_vars, temp_uuid):

        helper_functions.get_species_dataset_trait(self, start_vars)

        #tempdata = temp_data.TempData(temp_uuid)
        
        self.temp_uuid = temp_uuid #needed to pass temp_uuid to gn1 mapping code (marker_regression_gn1.py)

        self.json_data = {}
        self.json_data['lodnames'] = ['lod.hk']
        
        self.samples = [] # Want only ones with values
        self.vals = []

        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            self.samples.append(str(sample))
            self.vals.append(value)
 
        self.mapping_method = start_vars['method']
        if start_vars['manhattan_plot'] == "true":
            self.manhattan_plot = True
        else:
            self.manhattan_plot = False

        self.maf = start_vars['maf'] # Minor allele frequency
        self.suggestive = ""
        self.significant = ""
        self.pair_scan = False # Initializing this since it is checked in views to determine which template to use
        self.score_type = "LRS" #ZS: LRS or LOD
        self.mapping_scale = "physic"
        self.num_perm = 0

        #ZS: This is passed to GN1 code for single chr mapping
        self.selected_chr = -1        
        if "selected_chr" in start_vars:
            self.selected_chr = int(start_vars['selected_chr'])
 
        self.dataset.group.get_markers()
        if self.mapping_method == "gemma":
            self.score_type = "LOD"
            included_markers, p_values = gemma_mapping.run_gemma(self.dataset, self.samples, self.vals)
            self.dataset.group.get_specified_markers(markers = included_markers)
            self.dataset.group.markers.add_pvalues(p_values)
            results = self.dataset.group.markers.markers
        elif self.mapping_method == "rqtl_plink":
            results = self.run_rqtl_plink()
        elif self.mapping_method == "rqtl_geno":
            self.score_type = "LOD"
            self.mapping_scale = "morgan"
            if start_vars['num_perm'] == "":
                self.num_perm = 0
            else:
                self.num_perm = start_vars['num_perm']
            self.control = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            self.method = start_vars['mapmethod_rqtl_geno']
            self.model = start_vars['mapmodel_rqtl_geno']

            if start_vars['pair_scan'] == "true":
                self.pair_scan = True

            results = self.run_rqtl_geno()
        elif self.mapping_method == "reaper":
            if start_vars['num_perm'] == "":
                self.num_perm = 0
            else:
                self.num_perm = int(start_vars['num_perm'])
            self.additive = False
            self.control = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            results = self.gen_reaper_results()
        elif self.mapping_method == "plink":
            results = self.run_plink()
        elif self.mapping_method == "pylmm":
            print("RUNNING PYLMM")
            self.num_perm = start_vars['num_perm']
            if self.num_perm != "":
                if int(self.num_perm) > 0:
	             self.run_permutations(str(temp_uuid))
            results = self.gen_data(str(temp_uuid))
        else:
            print("RUNNING NOTHING")
            
        if self.pair_scan == True:  
            self.qtl_results = []
            highest_chr = 1 #This is needed in order to convert the highest chr to X/Y
            for marker in results:
                if marker['chr1'] > 0 or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                    if marker['chr1'] > highest_chr or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                        highest_chr = marker['chr1']
                    if 'lod_score' in marker.keys():
                        self.qtl_results.append(marker)

            for qtl in enumerate(self.qtl_results):
                self.json_data['chr1'].append(str(qtl['chr1']))
                self.json_data['chr2'].append(str(qtl['chr2']))
                self.json_data['Mb'].append(qtl['Mb'])
                self.json_data['markernames'].append(qtl['name'])

            self.js_data = dict(
                json_data = self.json_data,
                this_trait = self.this_trait.name,
                data_set = self.dataset.name,
                maf = self.maf,
                manhattan_plot = self.manhattan_plot,
                mapping_scale = self.mapping_scale,
                qtl_results = self.qtl_results,
            )

        else:
            self.cutoff = 2    
            self.qtl_results = []
            highest_chr = 1 #This is needed in order to convert the highest chr to X/Y
            for marker in results:
                if marker['chr'] > 0 or marker['chr'] == "X" or marker['chr'] == "X/Y":
                    if marker['chr'] > highest_chr or marker['chr'] == "X" or marker['chr'] == "X/Y":
                        highest_chr = marker['chr']
                    if ('lod_score' in marker.keys()) or ('lrs_value' in marker.keys()):
                        self.qtl_results.append(marker)

            self.json_data['chr'] = []
            self.json_data['pos'] = []
            self.json_data['lod.hk'] = []
            self.json_data['markernames'] = []

            self.json_data['suggestive'] = self.suggestive
            self.json_data['significant'] = self.significant

            #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
            for index, qtl in enumerate(self.qtl_results):
                #if index<40:
                #    print("lod score is:", qtl['lod_score'])
                if qtl['chr'] == highest_chr and highest_chr != "X" and highest_chr != "X/Y":
                    print("changing to X")
                    self.json_data['chr'].append("X")
                else:
                    self.json_data['chr'].append(str(qtl['chr']))
                self.json_data['pos'].append(qtl['Mb'])
                if 'lrs_value' in qtl.keys():
                    self.json_data['lod.hk'].append(str(qtl['lrs_value']))
                else:
                    self.json_data['lod.hk'].append(str(qtl['lod_score']))
                self.json_data['markernames'].append(qtl['name'])

            #Get chromosome lengths for drawing the interval map plot
            chromosome_mb_lengths = {}
            self.json_data['chrnames'] = []
            for key in self.species.chromosomes.chromosomes.keys():
                self.json_data['chrnames'].append([self.species.chromosomes.chromosomes[key].name, self.species.chromosomes.chromosomes[key].mb_length])
                chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length
        
            # print("json_data:", self.json_data)
        

            self.js_data = dict(
                result_score_type = self.score_type,
                json_data = self.json_data,
                this_trait = self.this_trait.name,
                data_set = self.dataset.name,
                maf = self.maf,
                manhattan_plot = self.manhattan_plot,
                mapping_scale = self.mapping_scale,
                chromosomes = chromosome_mb_lengths,
                qtl_results = self.qtl_results,
            )
        

    def run_gemma(self):
        """Generates p-values for each marker using GEMMA"""
        
        self.gen_pheno_txt_file()

        os.chdir("/home/zas1024/gene/web/gemma")

        gemma_command = './gemma -bfile %s -k output_%s.cXX.txt -lmm 1 -o %s_output' % (
                                                                                                 self.dataset.group.name,
                                                                                                 self.dataset.group.name,
                                                                                                 self.dataset.group.name)
        print("gemma_command:" + gemma_command)
        
        os.system(gemma_command)
        
        included_markers, p_values = self.parse_gemma_output()
        
        self.dataset.group.get_specified_markers(markers = included_markers)
        
        #for marker in self.dataset.group.markers.markers:
        #    if marker['name'] not in included_markers:
        #        print("marker:", marker)
        #        self.dataset.group.markers.markers.remove(marker)
        #        #del self.dataset.group.markers.markers[marker]
        
        self.dataset.group.markers.add_pvalues(p_values)

        return self.dataset.group.markers.markers


    def parse_gemma_output(self):
        included_markers = []
        p_values = []
        with open("/home/zas1024/gene/web/gemma/output/{}_output.assoc.txt".format(self.dataset.group.name)) as output_file:
            for line in output_file:
                if line.startswith("chr"):
                    continue
                else:
                    included_markers.append(line.split("\t")[1])
                    p_values.append(float(line.split("\t")[10]))
                    #p_values[line.split("\t")[1]] = float(line.split("\t")[10])
        #print("p_values: ", p_values)
        return included_markers, p_values

    def gen_pheno_txt_file(self):
        """Generates phenotype file for GEMMA"""
        
        #with open("/home/zas1024/gene/web/gemma/tmp_pheno/{}.txt".format(filename), "w") as outfile:
        #    for sample, i in enumerate(self.samples):
        #        print("sample:" + str(i))
        #        print("self.vals[i]:" + str(self.vals[sample]))
        #        outfile.write(str(i) + "\t" + str(self.vals[sample]) + "\n")
                
        with open("/home/zas1024/gene/web/gemma/{}.fam".format(self.dataset.group.name), "w") as outfile:
            for i, sample in enumerate(self.samples):
                outfile.write(str(sample) + " " + str(sample) + " 0 0 0 " + str(self.vals[i]) + "\n")

    #def gen_plink_for_gemma(self, filename):
    #    
    #    make_bed = "/home/zas1024/plink/plink --file /home/zas1024/plink/%s --noweb --no-fid --no-parents --no-sex --no-pheno --pheno %s%s.txt --out %s%s --make-bed" % (webqtlConfig.HTMLPATH,
    #                                                                                                                                             webqtlConfig.HTMLPATH,
    #                                                                                                                                             self.dataset.group.name,
    #                                                                                                                                             webqtlConfig.TMPDIR,
    #                                                                                                                                             filename,
    #                                                                                                                                             webqtlConfig.TMPDIR,
    #                                                                                                                                             filename)
    #
    #
    
    def run_rqtl_plink(self):
        os.chdir("/home/zas1024/plink")
        
        output_filename = webqtlUtil.genRandStr("%s_%s_"%(self.dataset.group.name, self.this_trait.name))
        
        self.gen_pheno_txt_file_plink(pheno_filename = output_filename)
        
        rqtl_command = './plink --noweb --ped %s.ped --no-fid --no-parents --no-sex --no-pheno --map %s.map --pheno %s/%s.txt --pheno-name %s --maf %s --missing-phenotype -9999 --out %s%s --assoc ' % (self.dataset.group.name, self.dataset.group.name, webqtlConfig.TMPDIR, plink_output_filename, self.this_trait.name, self.maf, webqtlConfig.TMPDIR, plink_output_filename)
        
        os.system(rqtl_command)
        
        count, p_values = self.parse_rqtl_output(plink_output_filename)

    def geno_to_rqtl_function(self):        # TODO: Need to figure out why some genofiles have the wrong format and don't convert properly
        print("Adding some custom helper functions to the R environment")



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
        """ % (self.dataset.group.name + ".geno"))
    
    def run_rqtl_geno(self):
        print("Calling R/qtl")

        self.geno_to_rqtl_function()

        ## Get pointers to some common R functions
        r_library     = ro.r["library"]                 # Map the library function
        r_c           = ro.r["c"]                       # Map the c function
        r_sum         = ro.r["sum"]                     # Map the sum function
        plot          = ro.r["plot"]                    # Map the plot function
        postscript    = ro.r["postscript"]              # Map the postscript function
        png           = ro.r["png"]              # Map the png function
        dev_off       = ro.r["dev.off"]                 # Map the device off function

        print(r_library("qtl"))                         # Load R/qtl

        ## Get pointers to some R/qtl functions
        scanone         = ro.r["scanone"]               # Map the scanone function
        scantwo         = ro.r["scantwo"]               # Map the scantwo function
        calc_genoprob   = ro.r["calc.genoprob"]         # Map the calc.genoprob function
        read_cross      = ro.r["read.cross"]            # Map the read.cross function
        write_cross     = ro.r["write.cross"]           # Map the write.cross function
        GENOtoCSVR      = ro.r["GENOtoCSVR"]            # Map the GENOtoCSVR function

        genofilelocation  = webqtlConfig.HTMLPATH + "genotypes/" + self.dataset.group.name + ".geno"
        crossfilelocation = webqtlConfig.HTMLPATH + "genotypes/" + self.dataset.group.name + ".cross"

        print("Conversion of geno to cross at location:", genofilelocation, " to ", crossfilelocation)

        cross_object = GENOtoCSVR(genofilelocation, crossfilelocation)                                  # TODO: Add the SEX if that is available

        if self.manhattan_plot:
            cross_object = calc_genoprob(cross_object)
        else:
            cross_object = calc_genoprob(cross_object, step=1, stepwidth="max")

        cross_object = self.add_phenotype(cross_object, self.sanitize_rqtl_phenotype())                 # Add the phenotype

        # for debug: write_cross(cross_object, "csvr", "test.csvr")

        # Scan for QTLs
        covar = self.create_covariates(cross_object)                                                    # Create the additive covariate matrix

        if self.pair_scan:
            if self.do_control == "true":                                                # If sum(covar) > 0 we have a covariate matrix
                print("Using covariate"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", addcovar = covar, model=self.model, method=self.method, n_cluster = 16)
            else:
                print("No covariates"); result_data_frame = scantwo(cross_object, pheno = "the_pheno", model=self.model, method=self.method, n_cluster = 16)
 
            print("Pair scan results:", result_data_frame)

            self.pair_scan_filename = webqtlUtil.genRandStr("scantwo_") + ".png"
            png(file=webqtlConfig.TMPDIR+self.pair_scan_filename)
            plot(result_data_frame)
            dev_off()
            
            return self.process_pair_scan_results(result_data_frame)

        else:
            if self.do_control == "true":
                print("Using covariate"); result_data_frame = scanone(cross_object, pheno = "the_pheno", addcovar = covar, model=self.model, method=self.method)
            else:
                print("No covariates"); result_data_frame = scanone(cross_object, pheno = "the_pheno", model=self.model, method=self.method)

            if int(self.num_perm) > 0:                                                                   # Do permutation (if requested by user)
                if self.do_control == "true":
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", addcovar = covar, n_perm = int(self.num_perm), model=self.model, method=self.method)
                else:
                    perm_data_frame = scanone(cross_object, pheno_col = "the_pheno", n_perm = int(self.num_perm), model=self.model, method=self.method)

                self.process_rqtl_perm_results(perm_data_frame)                                          # Functions that sets the thresholds for the webinterface

            return self.process_rqtl_results(result_data_frame)

    def add_phenotype(self, cross, pheno_as_string):
        ro.globalenv["the_cross"] = cross
        ro.r('the_cross$pheno <- cbind(pull.pheno(the_cross), the_pheno = '+ pheno_as_string +')')
        return ro.r["the_cross"]

    def create_covariates(self, cross):
        ro.globalenv["the_cross"] = cross
        ro.r('genotypes <- pull.geno(the_cross)')                             # Get the genotype matrix
        userinputS = self.control.replace(" ", "").split(",")                 # TODO: sanitize user input, Never Ever trust a user
        covariate_names = ', '.join('"{0}"'.format(w) for w in userinputS)
        print("Marker names of selected covariates:", covariate_names)
        ro.r('covnames <- c(' + covariate_names + ')')
        ro.r('covInGeno <- which(covnames %in% colnames(genotypes))')
        ro.r('covnames <- covnames[covInGeno]')
        ro.r("cat('covnames (purged): ', covnames,'\n')")
        ro.r('covariates <- genotypes[,covnames]')                            # Get the covariate matrix by using the marker name as index to the genotype file
        print("R/qtl matrix of covariates:", ro.r["covariates"])
        return ro.r["covariates"]

    def sanitize_rqtl_phenotype(self):
        pheno_as_string = "c("
        for i, val in enumerate(self.vals):
            if val == "x":
                if i < (len(self.vals) - 1):
                    pheno_as_string +=  "NA,"
                else:
                    pheno_as_string += "NA"
            else:
                if i < (len(self.vals) - 1):
                    pheno_as_string += str(val) + ","
                else:
                    pheno_as_string += str(val)
        pheno_as_string += ")"
        return pheno_as_string

    def process_pair_scan_results(self, result):
        pair_scan_results = []

        result = result[1]
        output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]
        print("R/qtl scantwo output:", output)

        for i, line in enumerate(result.iter_row()):
            marker = {}
            marker['name'] = result.rownames[i]
            marker['chr1'] = output[i][0]
            marker['Mb'] = output[i][1]
            marker['chr2'] = int(output[i][2])
            pair_scan_results.append(marker)

        print("pair_scan_results:", pair_scan_results)

        return pair_scan_results

    def process_rqtl_results(self, result):        # TODO: how to make this a one liner and not copy the stuff in a loop
        qtl_results = []

        output = [tuple([result[j][i] for j in range(result.ncol)]) for i in range(result.nrow)]
        print("R/qtl scanone output:", output)

        for i, line in enumerate(result.iter_row()):
            marker = {}
            marker['name'] = result.rownames[i]
            marker['chr'] = output[i][0]
            marker['Mb'] = output[i][1]
            marker['lod_score'] = output[i][2]
            qtl_results.append(marker)

        return qtl_results

    def process_rqtl_perm_results(self, results):
        perm_vals = []
        for line in str(results).split("\n")[1:(int(self.num_perm)+1)]:
            print("R/qtl permutation line:", line.split())
            perm_vals.append(float(line.split()[1]))

        self.suggestive = np.percentile(np.array(perm_vals), 67)
        self.significant = np.percentile(np.array(perm_vals), 95)

        return self.suggestive, self.significant


    def run_plink(self):
        plink_output_filename = webqtlUtil.genRandStr("%s_%s_"%(self.dataset.group.name, self.this_trait.name))
        
        self.gen_pheno_txt_file_plink(pheno_filename = plink_output_filename)
        
        plink_command = PLINK_COMMAND + ' --noweb --ped %s/%s.ped --no-fid --no-parents --no-sex --no-pheno --map %s/%s.map --pheno %s%s.txt --pheno-name %s --maf %s --missing-phenotype -9999 --out %s%s --assoc ' % (PLINK_PATH, self.dataset.group.name, PLINK_PATH, self.dataset.group.name, webqtlConfig.TMPDIR, plink_output_filename, self.this_trait.name, self.maf, webqtlConfig.TMPDIR, plink_output_filename)
        print("plink_command:", plink_command)        

        os.system(plink_command)

        count, p_values = self.parse_plink_output(plink_output_filename)
        
        #for marker in self.dataset.group.markers.markers:
        #    if marker['name'] not in included_markers:
        #        print("marker:", marker)
        #        self.dataset.group.markers.markers.remove(marker)
        #        #del self.dataset.group.markers.markers[marker]
        
        print("p_values:", pf(p_values))
        
        self.dataset.group.markers.add_pvalues(p_values)

        return self.dataset.group.markers.markers
   

    def gen_pheno_txt_file_plink(self, pheno_filename = ''):
        ped_sample_list = self.get_samples_from_ped_file()	
        output_file = open("%s%s.txt" % (webqtlConfig.TMPDIR, pheno_filename), "wb")
        header = 'FID\tIID\t%s\n' % self.this_trait.name
        output_file.write(header)
    
        new_value_list = []
        
        #if valueDict does not include some strain, value will be set to -9999 as missing value
        for i, sample in enumerate(ped_sample_list):
            try:
                value = self.vals[i]
                value = str(value).replace('value=','')
                value = value.strip()
            except:
                value = -9999
    
            new_value_list.append(value)
            
            
        new_line = ''
        for i, sample in enumerate(ped_sample_list):
            j = i+1
            value = new_value_list[i]
            new_line += '%s\t%s\t%s\n'%(sample, sample, value)
            
            if j%1000 == 0:
                output_file.write(newLine)
                new_line = ''
        
        if new_line:
            output_file.write(new_line)
            
        output_file.close()
        
    def gen_pheno_txt_file_rqtl(self, pheno_filename = ''):
        ped_sample_list = self.get_samples_from_ped_file()	
        output_file = open("%s%s.txt" % (webqtlConfig.TMPDIR, pheno_filename), "wb")
        header = 'FID\tIID\t%s\n' % self.this_trait.name
        output_file.write(header)
    
        new_value_list = []
        
        #if valueDict does not include some strain, value will be set to -9999 as missing value
        for i, sample in enumerate(ped_sample_list):
            try:
                value = self.vals[i]
                value = str(value).replace('value=','')
                value = value.strip()
            except:
                value = -9999
    
            new_value_list.append(value)
            
            
        new_line = ''
        for i, sample in enumerate(ped_sample_list):
            j = i+1
            value = new_value_list[i]
            new_line += '%s\t%s\t%s\n'%(sample, sample, value)
            
            if j%1000 == 0:
                output_file.write(newLine)
                new_line = ''
        
        if new_line:
            output_file.write(new_line)
            
        output_file.close()
    
    # get strain name from ped file in order
    def get_samples_from_ped_file(self):
        ped_file= open("{}/{}.ped".format(PLINK_PATH, self.dataset.group.name),"r")
        line = ped_file.readline()
        sample_list=[]
        
        while line:
            lineList = string.split(string.strip(line), '\t')
            lineList = map(string.strip, lineList)
            
            sample_name = lineList[0]
            sample_list.append(sample_name)
            
            line = ped_file.readline()
        
        return sample_list
    
    def gen_reaper_results(self):
        genotype = self.dataset.group.read_genotype_file()

        samples, values, variances = self.this_trait.export_informative()

        trimmed_samples = []
        trimmed_values = []
        for i in range(0, len(samples)):
            if samples[i] in self.dataset.group.samplelist:
                trimmed_samples.append(samples[i])
                trimmed_values.append(values[i])
                
        self.lrs_array = genotype.permutation(strains = trimmed_samples,
                                                   trait = trimmed_values, 
                                                   nperm= self.num_perm)
        
        self.suggestive = self.lrs_array[int(self.num_perm*0.37-1)]
        self.significant = self.lrs_array[int(self.num_perm*0.95-1)]
        self.json_data['suggestive'] = self.suggestive
        self.json_data['significant'] = self.significant

        print("samples:", trimmed_samples)

        if self.control != "" and self.do_control == "true":
            print("CONTROL IS:", self.control)
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values,
                                                          control = str(self.control))
        else:
            reaper_results = genotype.regression(strains = trimmed_samples,
                                                          trait = trimmed_values)

        self.json_data['chr'] = []
        self.json_data['pos'] = []
        self.json_data['lod.hk'] = []
        self.json_data['markernames'] = []
        if self.additive:
            self.json_data['additive'] = []

        #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
        qtl_results = []
        for qtl in reaper_results:
            reaper_locus = qtl.locus
            #ZS: Convert chr to int
            converted_chr = reaper_locus.chr
            if reaper_locus.chr != "X" and reaper_locus.chr != "X/Y":
                converted_chr = int(reaper_locus.chr)
            self.json_data['chr'].append(converted_chr)
            self.json_data['pos'].append(reaper_locus.Mb)
            self.json_data['lod.hk'].append(qtl.lrs)
            self.json_data['markernames'].append(reaper_locus.name)
            if self.additive:
                self.json_data['additive'].append(qtl.additive)
            locus = {"name":reaper_locus.name, "chr":reaper_locus.chr, "cM":reaper_locus.cM, "Mb":reaper_locus.Mb}
            qtl = {"lrs_value": qtl.lrs, "chr":converted_chr, "Mb":reaper_locus.Mb,
                   "cM":reaper_locus.cM, "name":reaper_locus.name, "additive":qtl.additive, "dominance":qtl.dominance}
            qtl_results.append(qtl)

        return qtl_results


    def parse_plink_output(self, output_filename):
        plink_results={}
    
        threshold_p_value = 0.01
    
        result_fp = open("%s%s.qassoc"% (webqtlConfig.TMPDIR, output_filename), "rb")
        
        header_line = result_fp.readline()# read header line
        line = result_fp.readline()
        
        value_list = [] # initialize value list, this list will include snp, bp and pvalue info
        p_value_dict = {}
        count = 0
        
        while line:
            #convert line from str to list
            line_list = self.build_line_list(line=line)
    
            # only keep the records whose chromosome name is in db
            if self.species.chromosomes.chromosomes.has_key(int(line_list[0])) and line_list[-1] and line_list[-1].strip()!='NA':
    
                chr_name = self.species.chromosomes.chromosomes[int(line_list[0])]
                snp = line_list[1]
                BP = line_list[2]
                p_value = float(line_list[-1])
                if threshold_p_value >= 0 and threshold_p_value <= 1:
                    if p_value < threshold_p_value:
                        p_value_dict[snp] = float(p_value)
                
                if plink_results.has_key(chr_name):
                    value_list = plink_results[chr_name]
                    
                    # pvalue range is [0,1]
                    if threshold_p_value >=0 and threshold_p_value <= 1:
                        if p_value < threshold_p_value:
                            value_list.append((snp, BP, p_value))
                            count += 1
                    
                    plink_results[chr_name] = value_list
                    value_list = []
                else:
                    if threshold_p_value >= 0 and threshold_p_value <= 1:
                        if p_value < threshold_p_value:
                            value_list.append((snp, BP, p_value))
                            count += 1

                    if value_list:
                        plink_results[chr_name] = value_list

                    value_list=[]

                line = result_fp.readline()
            else:
                line = result_fp.readline()

        #if p_value_list:
        #    min_p_value = min(p_value_list)
        #else:
        #    min_p_value = 0
            
        return count, p_value_dict
    
    ######################################################
    # input: line: str,one line read from file
    # function: convert line from str to list; 
    # output: lineList list
    #######################################################
    def build_line_list(self, line=None):
        
        line_list = string.split(string.strip(line),' ')# irregular number of whitespaces between columns
        line_list = [item for item in line_list if item <>'']
        line_list = map(string.strip, line_list)
    
        return line_list
    
    
    def run_permutations(self, temp_uuid):
        """Runs permutations and gets significant and suggestive LOD scores"""

        top_lod_scores = []
	
        print("self.num_perm:", self.num_perm)

        for permutation in range(int(self.num_perm)):

            pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])
            np.random.shuffle(pheno_vector)

            key = "pylmm:input:" + temp_uuid
        
            if self.dataset.group.species == "human":
                p_values, t_stats = self.gen_human_results(pheno_vector, key, temp_uuid)
            else:
                genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
                
                no_val_samples = self.identify_empty_samples()
                trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
                
                genotype_matrix = np.array(trimmed_genotype_data).T
    
                params = dict(pheno_vector = pheno_vector.tolist(),
                            genotype_matrix = genotype_matrix.tolist(),
                            restricted_max_likelihood = True,
                            refit = False,
                            temp_uuid = temp_uuid,
                            
                            # meta data
                            timestamp = datetime.datetime.now().isoformat(),
                            )
                
                json_params = json.dumps(params)
                Redis.set(key, json_params)
                Redis.expire(key, 60*60)
    
                command = PYLMM_COMMAND+' --key {} --species {}'.format(key,"other")
    
                os.system(command)
    
                
                json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
                results = json.loads(json_results[1])
                p_values = [float(result) for result in results['p_values']]
                
                lowest_p_value = 1
                for p_value in p_values:
                    if p_value < lowest_p_value:
                        lowest_p_value = p_value
                
                print("lowest_p_value:", lowest_p_value)        
                top_lod_scores.append(-math.log10(lowest_p_value))

        print("top_lod_scores:", top_lod_scores)

        self.suggestive = np.percentile(top_lod_scores, 67)
        self.significant = np.percentile(top_lod_scores, 95)

    def gen_data(self, temp_uuid):
        """Generates p-values for each marker"""


        print("self.vals is:", self.vals)
        pheno_vector = np.array([(val == "x" or val == "") and np.nan or float(val) for val in self.vals])

        #lmm_uuid = str(uuid.uuid4())

        key = "pylmm:input:" + temp_uuid
        print("key is:", pf(key))
        #with Bench("Loading cache"):
        #    result = Redis.get(key)

        if self.dataset.group.species == "human":
            p_values, t_stats = self.gen_human_results(pheno_vector, key, temp_uuid)
            #p_values = self.trim_results(p_values)
            
        else:
            print("NOW CWD IS:", os.getcwd())
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
            
            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
            
            genotype_matrix = np.array(genotype_data).T

            #print("pheno_vector: ", pf(pheno_vector))
            #print("genotype_matrix: ", pf(genotype_matrix))
            #print("genotype_matrix.shape: ", pf(genotype_matrix.shape))

            #params = {"pheno_vector": pheno_vector,
            #            "genotype_matrix": genotype_matrix,
            #            "restricted_max_likelihood": True,
            #            "refit": False,
            #            "temp_data": tempdata}
            
            # print("genotype_matrix:", str(genotype_matrix.tolist()))
            # print("pheno_vector:", str(pheno_vector.tolist()))
            
            params = dict(pheno_vector = pheno_vector.tolist(),
                        genotype_matrix = genotype_matrix.tolist(),
                        restricted_max_likelihood = True,
                        refit = False,
                        temp_uuid = temp_uuid,
                        
                        # meta data
                        timestamp = datetime.datetime.now().isoformat(),
                        )
            
            json_params = json.dumps(params)
            #print("json_params:", json_params)
            Redis.set(key, json_params)
            Redis.expire(key, 60*60)
            print("before printing command")

            command = PYLMM_COMMAND + ' --key {} --species {}'.format(key,
                                                                                                                    "other")
            print("command is:", command)
            print("after printing command")

            os.system(command)

            #t_stats, p_values = lmm.run(key)
            #lmm.run(key)
            
            json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
            results = json.loads(json_results[1])
            p_values = [float(result) for result in results['p_values']]
            #print("p_values:", p_values[:10])
            #p_values = self.trim_results(p_values)
            t_stats = results['t_stats']
            
            #t_stats, p_values = lmm.run(
            #    pheno_vector,
            #    genotype_matrix,
            #    restricted_max_likelihood=True,
            #    refit=False,
            #    temp_data=tempdata
            #)
            #print("p_values:", p_values)

        self.dataset.group.markers.add_pvalues(p_values)
        
        #self.get_lod_score_cutoff()
        
        return self.dataset.group.markers.markers

    def trim_results(self, p_values):
        print("len_p_values:", len(p_values))
        if len(p_values) > 500:
            p_values.sort(reverse=True)
            trimmed_values = p_values[:500]
        
        return trimmed_values

    #def gen_human_results(self, pheno_vector, tempdata):
    def gen_human_results(self, pheno_vector, key, temp_uuid):
        file_base = os.path.join(webqtlConfig.PYLMM_PATH, self.dataset.group.name)
        print("file_base:", file_base)

        plink_input = input.plink(file_base, type='b')
        input_file_name = os.path.join(webqtlConfig.SNP_PATH, self.dataset.group.name + ".snps.gz")

        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))

        print("Before creating params")

        params = dict(pheno_vector = pheno_vector.tolist(),
                    covariate_matrix = covariate_matrix.tolist(),
                    input_file_name = input_file_name,
                    kinship_matrix = kinship_matrix.tolist(),
                    refit = False,
                    temp_uuid = temp_uuid,
                        
                    # meta data
                    timestamp = datetime.datetime.now().isoformat(),
                    )
        
        print("After creating params")
        
        json_params = json.dumps(params)
        Redis.set(key, json_params)
        Redis.expire(key, 60*60)

        print("Before creating the command")

        command = PYLMM_COMMAND+' --key {} --species {}'.format(key,
                                                                                                                "human")
        
        print("command is:", command)
        
        os.system(command)
        
        json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
        results = json.loads(json_results[1])
        t_stats = results['t_stats']
        p_values = results['p_values']
        

        #p_values, t_stats = lmm.run_human(key)

        #p_values, t_stats = lmm.run_human(
        #        pheno_vector,
        #        covariate_matrix,
        #        input_file_name,
        #        kinship_matrix,
        #        loading_progress=tempdata
        #    )

        return p_values, t_stats

    def get_lod_score_cutoff(self):
        print("INSIDE GET LOD CUTOFF")
        high_qtl_count = 0
        for marker in self.dataset.group.markers.markers:
            if marker['lod_score'] > 1:
                high_qtl_count += 1

        if high_qtl_count > 1000:
            return 1
        else:
            return 0

    def identify_empty_samples(self):
        no_val_samples = []
        for sample_count, val in enumerate(self.vals):
            if val == "x":
                no_val_samples.append(sample_count)
        return no_val_samples
        
    def trim_genotypes(self, genotype_data, no_value_samples):
        trimmed_genotype_data = []
        for marker in genotype_data:
            new_genotypes = []
            for item_count, genotype in enumerate(marker):
                if item_count in no_value_samples:
                    continue
                try:
                    genotype = float(genotype)
                except ValueError:
                    genotype = np.nan
                    pass
                new_genotypes.append(genotype)
            trimmed_genotype_data.append(new_genotypes)
        return trimmed_genotype_data
    
def create_snp_iterator_file(group):
    plink_file_base = os.path.join(webqtlConfig.PYLMM_PATH, group)
    plink_input = input.plink(plink_file_base, type='b')
    
    data = dict(plink_input = list(plink_input),
                numSNPs = plink_input.numSNPs)
    
    #input_dict = {}
    #
    #input_dict['plink_input'] = list(plink_input)
    #input_dict['numSNPs'] = plink_input.numSNPs
    #
    
    snp_file_base = os.path.join(webqtlConfig.SNP_PATH, group + ".snps.gz")
    
    with gzip.open(snp_file_base, "wb") as fh:
        pickle.dump(data, fh, pickle.HIGHEST_PROTOCOL)

#if __name__ == '__main__':
#    import cPickle as pickle
#    import gzip
#    create_snp_iterator_file("HLC")
    
if __name__ == '__main__':
    import cPickle as pickle
    import gzip
    create_snp_iterator_file("HLC")
