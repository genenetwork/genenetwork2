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

from pprint import pformat as pf

from htmlgen import HTMLgen2 as HT
import reaper

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.trait import GeneralTrait
from base import data_set
from base.templatePage import templatePage
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
        
        self.get_trait_db_obs(trait_db_list)
        
        self.corr_results = {}
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]
            
            this_db_samples = this_db.group.samplelist
            this_sample_data = this_trait.data
            print("this_sample_data", len(this_sample_data))
            
            corr_result_row = {}

            for target in self.trait_list:
                target_trait = target[0]
                target_db = target[1]
		target_samples = target_db.group.samplelist
                
                if this_trait == target_trait and this_db == target_db:
                    corr_result_row[this_trait.name] = {'sample_r': 1,
                                                        'sample_p': 0,
                                                        'num_overlap': len(target_samples),
							'this_trait': this_trait.name,
							'this_db': this_trait.dataset.name,
                                                        'target_trait': this_trait.name,
                                                        'target_db': this_trait.dataset.name}
                    continue

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
        
                #print("this_trait_vals:", this_trait_vals)
                #print("target_vals:", target_vals)
        
                this_trait_vals, target_vals, num_overlap = corr_result_helpers.normalize_values(
                this_trait_vals, target_vals)
                
                sample_r, sample_p = scipy.stats.pearsonr(this_trait_vals, target_vals)

                corr_matrix_cell = {'sample_r': sample_r,
                                    'sample_p': sample_p,
                                    'num_overlap': num_overlap,
				    'this_trait': this_trait.name,
                                    'this_db': this_trait.dataset.name,
                                    'target_trait': target_trait.name,
                                    'target_db': target_trait.dataset.name}
                
                corr_result_row[target_trait.name] = corr_matrix_cell
                
            self.corr_results[this_trait.name] = corr_result_row
            
        print("corr_results:", pf(self.corr_results))
        
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

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
