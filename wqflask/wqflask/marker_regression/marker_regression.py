from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import os
import collections

import numpy as np

import simplejson as json

#from redis import Redis

from utility import Plot, Bunch
from base.trait import GeneralTrait
from base import data_set
from base import species
from utility import helper_functions
from base import webqtlConfig
from wqflask.my_pylmm.data import prep_data
from wqflask.my_pylmm.pyLMM import lmm
from utility import temp_data

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

        genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]

        no_val_samples = self.identify_empty_samples()
        trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)

        pheno_vector = np.array([float(val) for val in self.vals if val!="x"])
        genotype_matrix = np.array(trimmed_genotype_data).T

        t_stats, p_values = lmm.run(
            pheno_vector,
            genotype_matrix,
            restricted_max_likelihood=True,
            refit=False,
            temp_data=tempdata
        )
        
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
