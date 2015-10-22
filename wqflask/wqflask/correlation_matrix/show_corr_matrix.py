## Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Dr. Robert W. Williams at rwilliams@uthsc.edu
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)

from __future__ import absolute_import, print_function, division

import sys
sys.path.append(".")

import gc
import string
import cPickle
import os
import time
import pp
import math
import collections
import resource

import scipy

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects

from pprint import pformat as pf

from htmlgen import HTMLgen2 as HT
import reaper

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.trait import GeneralTrait
from base import data_set
from utility import webqtlUtil, helper_functions, corr_result_helpers
from dbFunction import webqtlDatabaseFunction
import utility.webqtlUtil #this is for parallel computing only.
from wqflask.correlation import correlation_functions
from utility.benchmark import Bench

from MySQLdb import escape_string as escape

from pprint import pformat as pf

from flask import Flask, g


class CorrelationMatrix(object):
    
    def __init__(self, start_vars):
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        
        helper_functions.get_trait_db_obs(self, trait_db_list)

        self.all_sample_list = []
        self.traits = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            self.traits.append(this_trait)
            this_sample_data = this_trait.data
            
            for sample in this_sample_data:
                if sample not in self.all_sample_list:
                    self.all_sample_list.append(sample)

        self.sample_data = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_sample_data = this_trait.data
            
            #self.sample_data[this_trait.name] = []
            this_trait_vals = []
            for sample in self.all_sample_list:
                if sample in this_sample_data:
                    this_trait_vals.append(this_sample_data[sample].value)
                    #self.sample_data[this_trait.name].append(this_sample_data[sample].value)
                else:
                    this_trait_vals.append('')
                    #self.sample_data[this_trait.name].append('')
            self.sample_data.append(this_trait_vals)

        self.lowest_overlap = 8 #ZS: Variable set to the lowest overlapping samples in order to notify user, or 8, whichever is lower (since 8 is when we want to display warning)

        self.corr_results = []
        self.pca_corr_results = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]
            
            this_db_samples = this_db.group.samplelist
            this_sample_data = this_trait.data
            
            corr_result_row = []
            pca_corr_result_row = []
            is_spearman = False #ZS: To determine if it's above or below the diagonal
            for target in self.trait_list:
                target_trait = target[0]
                target_db = target[1]
                target_samples = target_db.group.samplelist

                target_sample_data = target_trait.data
                print("target_samples", len(target_samples))
                
                this_trait_vals = []
                target_vals = []
                for index, sample in enumerate(target_samples):
                    
                    if (sample in this_sample_data) and (sample in target_sample_data):
                        sample_value = this_sample_data[sample].value
                        target_sample_value = target_sample_data[sample].value
                        this_trait_vals.append(sample_value)
                        target_vals.append(target_sample_value)
        
                this_trait_vals, target_vals, num_overlap = corr_result_helpers.normalize_values(this_trait_vals, target_vals)

                if num_overlap < self.lowest_overlap:
                    self.lowest_overlap = num_overlap
                if num_overlap == 0:
                    corr_result_row.append([target_trait, 0, num_overlap])
                    pca_corr_result_row.append(0)
                else:
                    pearson_r, pearson_p = scipy.stats.pearsonr(this_trait_vals, target_vals)
                    if is_spearman == False:
                        sample_r, sample_p = pearson_r, pearson_p
                        if sample_r == 1:
                            is_spearman = True
                    else:
                        sample_r, sample_p = scipy.stats.spearmanr(this_trait_vals, target_vals)

                    corr_result_row.append([target_trait, sample_r, num_overlap])
                    pca_corr_result_row.append(pearson_r)
                
            self.corr_results.append(corr_result_row)
            self.pca_corr_results.append(pca_corr_result_row)

        print("corr_results:", pf(self.corr_results))

        groups = []
        for sample in self.all_sample_list:
            groups.append(1)

        pca = self.calculate_pca(self.pca_corr_results, range(len(self.traits)))

        self.loadings_array = self.process_loadings()

        self.js_data = dict(traits = [trait.name for trait in self.traits],
                            groups = groups,
                            cols = range(len(self.traits)),
                            rows = range(len(self.traits)),
                            samples = self.all_sample_list,
                            sample_data = self.sample_data,)
        #                    corr_results = [result[1] for result in result_row for result_row in self.corr_results])


        #self.js_data = dict(traits = self.traits,
        #                    groups = groups,
        #                    cols = range(len(self.traits)),
        #                    rows = range(len(self.traits)),
        #                    samples = self.all_sample_list,
        #                    sample_data = self.sample_data,
        #                    corr_results = self.corr_results,)
        
        
        
    def get_trait_db_obs(self, trait_db_list):
    
        self.trait_list = []
        for i, trait_db in enumerate(trait_db_list):
            if i == (len(trait_db_list) - 1):
                break
            trait_name, dataset_name = trait_db.split(":")
            #print("dataset_name:", dataset_name)
            dataset_ob = data_set.create_dataset(dataset_name)
            trait_ob = GeneralTrait(dataset=dataset_ob,
                                   name=trait_name,
                                   cellid=None)
            self.trait_list.append((trait_ob, dataset_ob))
            
        #print("trait_list:", self.trait_list)

        
    def calculate_pca(self, corr_results, cols): 
        base = importr('base')
        stats = importr('stats')        
        print("checking:", pf(stats.rnorm(100)))

        corr_results_to_list = robjects.FloatVector([item for sublist in corr_results for item in sublist])
        print("corr_results:",  pf(corr_results_to_list))

        m = robjects.r.matrix(corr_results_to_list, nrow=len(cols))
        eigen = base.eigen(m)
        print("eigen:", eigen)
        pca = stats.princomp(m, cor = "TRUE")
        print("pca:", pca)
        self.loadings = pca.rx('loadings')
        self.scores = pca.rx('scores')
        self.scale = pca.rx('scale')
        print("scores:", pca.rx('scores'))
        print("scale:", pca.rx('scale'))

        return pca

    def process_loadings(self):
        loadings_array = []
        loadings_row = []
        print("before loop:", self.loadings[0])
        for i in range(len(self.trait_list)):
            loadings_row = []
            for j in range(3):
                position = i + len(self.trait_list)*j
                loadings_row.append(self.loadings[0][position])
            loadings_array.append(loadings_row)
        print("loadings:", loadings_array)
        return loadings_array

