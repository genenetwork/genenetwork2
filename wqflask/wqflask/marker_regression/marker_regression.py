from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import sys
import os
import collections

import numpy as np
from scipy import linalg

#from redis import Redis


from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from wqflask.my_pylmm.data import prep_data
from wqflask.my_pylmm.pyLMM import lmm
from wqflask.my_pylmm.pyLMM import input
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data

from utility.benchmark import Bench


class MarkerRegression(object):

    def __init__(self, start_vars, temp_uuid):

        helper_functions.get_species_dataset_trait(self, start_vars)

        tempdata = temp_data.TempData(temp_uuid)
        
        self.samples = [] # Want only ones with values
        self.vals = []

        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            self.samples.append(str(sample))
            self.vals.append(value)
 
        self.gen_data(tempdata)

        #Get chromosome lengths for drawing the manhattan plot
        chromosome_mb_lengths = {}
        for key in self.species.chromosomes.chromosomes.keys():
            chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length
        
        self.js_data = dict(
            chromosomes = chromosome_mb_lengths,
            qtl_results = self.qtl_results,
        )
        


    def gen_data(self, tempdata):
        """Generates p-values for each marker"""


        file_base = os.path.join(webqtlConfig.PYLMM_PATH, self.dataset.group.name)
        
        plink_input = input.plink(file_base, type='b')
        
        
        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])
        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))
        
        refit = False
        
        v = np.isnan(pheno_vector)
        keep = True - v
        keep = keep.reshape((len(keep),))
        eigen_values = []
        eigen_vectors = []
        
        
        print("pheno_vector shape is: ", pf(pheno_vector.shape))
        
        #print("pheno_vector is: ", pf(pheno_vector))
        #print("kinship_matrix is: ", pf(kinship_matrix))
        
        if v.sum():
            pheno_vector = pheno_vector[keep]
            print("pheno_vector shape is now: ", pf(pheno_vector.shape))
            covariate_matrix = covariate_matrix[keep,:]
            print("kinship_matrix shape is: ", pf(kinship_matrix.shape))
            print("len(keep) is: ", pf(keep.shape))
            kinship_matrix = kinship_matrix[keep,:][:,keep]
            
        #if not v.sum():
        #    eigen_values = np.fromfile(file_base + ".kin.kva")
        #    eigen_vectors = np.fromfile(file_base + ".kin.kve")
            
        #print("eigen_values is: ", pf(eigen_values))
        #print("eigen_vectors is: ", pf(eigen_vectors))
            
        n = kinship_matrix.shape[0]
        lmm_ob = lmm.LMM(pheno_vector,
                         kinship_matrix,
                         eigen_values,
                         eigen_vectors,
                         covariate_matrix)
        lmm_ob.fit()

        # Buffers for pvalues and t-stats
        p_values = []
        t_statistics = []
        count = 0
        
        plink_input.getSNPIterator()
        print("# snps is: ", pf(plink_input.numSNPs))
        with Bench("snp iterator loop"):
            for snp, this_id in plink_input:
                #if count > 10000:
                #    break            
                count += 1
                
                x = snp[keep].reshape((n,1))
                #x[[1,50,100,200,3000],:] = np.nan
                v = np.isnan(x).reshape((-1,))
                
                # Check SNPs for missing values
                if v.sum():
                    keeps = True - v
                    xs = x[keeps,:]
                    # If no variation at this snp or all genotypes missing 
                    if keeps.sum() <= 1 or xs.var() <= 1e-6:
                        p_values.append(np.nan)
                        t_statistics.append(np.nan)
                        continue
            
                    # Its ok to center the genotype -  I used options.normalizeGenotype to
                    # force the removal of missing genotypes as opposed to replacing them with MAF.
                    
                    #if not options.normalizeGenotype:
                    #    xs = (xs - xs.mean()) / np.sqrt(xs.var())
                    
                    filtered_pheno = pheno_vector[keeps]
                    filtered_covariate_matrix = covariate_matrix[keeps,:]
                    filtered_kinship_matrix = kinship_matrix[keeps,:][:,keeps]
                    filtered_lmm_ob = lmm.LMM(filtered_pheno,filtered_kinship_matrix,X0=filtered_covariate_matrix)
                    if refit:
                        filtered_lmm_ob.fit(X=xs)
                    else:
                        #try:
                        filtered_lmm_ob.fit()
                        #except: pdb.set_trace()
                    ts,ps,beta,betaVar = Ls.association(xs,returnBeta=True)
                else:
                    if x.var() == 0:
                        p_values.append(np.nan)
                        t_statistics.append(np.nan)
                        continue
            
                    if refit:
                        lmm_ob.fit(X=x)
                    ts,ps,beta,betaVar = lmm_ob.association(x)
                p_values.append(ps)
                t_statistics.append(ts)
        

        #genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
        #
        #no_val_samples = self.identify_empty_samples()
        #trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
        #
        #genotype_matrix = np.array(trimmed_genotype_data).T
        #
        #print("pheno_vector is: ", pf(pheno_vector))
        #print("genotype_matrix is: ", pf(genotype_matrix))
        #
        #t_stats, p_values = lmm.run(
        #    pheno_vector,
        #    genotype_matrix,
        #    restricted_max_likelihood=True,
        #    refit=False,
        #    temp_data=tempdata
        #)
        
        print("p_values is: ", pf(p_values))
        self.dataset.group.markers.add_pvalues(p_values)

        #self.lrs_values = [marker['lrs_value'] for marker in self.dataset.group.markers.markers]
        #lrs_values_sorted = sorted(self.lrs_values)
        #
        #lrs_values_length = len(lrs_values_sorted)
        #
        #def lrs_threshold(place):
        #    return lrs_values_sorted[int((lrs_values_length * place) -1)]
        #
        #self.lrs_thresholds = Bunch(
        #                    suggestive = lrs_threshold(.37),
        #                    significant = lrs_threshold(.95),
        #                    highly_significant = lrs_threshold(.99),
        #                        )

        self.qtl_results = self.dataset.group.markers.markers

        for marker in self.qtl_results:
            if marker['lrs_value'] > webqtlConfig.MAXLRS:
                marker['lrs_value'] = webqtlConfig.MAXLRS

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
    
    
