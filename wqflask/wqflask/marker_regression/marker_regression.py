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

import simplejson as json

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

        self.dataset.group.get_markers()

        pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])

        if self.dataset.group.species == "human":
            p_values, t_stats = self.gen_human_results(pheno_vector, tempdata)
        else:
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]
            
            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)
            
            genotype_matrix = np.array(trimmed_genotype_data).T
            
            print("pheno_vector is: ", pf(pheno_vector))
            print("genotype_matrix is: ", pf(genotype_matrix))
            
            t_stats, p_values = lmm.run(
                pheno_vector,
                genotype_matrix,
                restricted_max_likelihood=True,
                refit=False,
                temp_data=tempdata
            )
        
        self.dataset.group.markers.add_pvalues(p_values)

        self.qtl_results = self.dataset.group.markers.markers


    def gen_human_results(self, pheno_vector, tempdata):
        file_base = os.path.join(webqtlConfig.PYLMM_PATH, self.dataset.group.name)

        plink_input = input.plink(file_base, type='b')

        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))

        p_values, t_stats = lmm.run_human(
                pheno_vector,
                covariate_matrix,
                plink_input,
                kinship_matrix,
                loading_progress=tempdata
            )

        return p_values, t_stats


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
    inputs = list(plink_input)
    
    snp_file_base = os.path.join(webqtlConfig.SNP_PATH, group + ".snps")
    
    with open(snp_file_base, "w") as fh:
        pickle.dump(inputs, fh)
    

if __name__ == '__main__':
    import cPickle as pickle
    create_snp_iterator_file("HLC")
