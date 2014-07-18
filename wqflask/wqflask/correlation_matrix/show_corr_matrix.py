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
        
        helper_functions.get_trait_db_obs(trait_db_list)

        self.all_sample_list = []
        self.traits = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            self.traits.append(this_trait.name)
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

        self.corr_results = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]
            
            this_db_samples = this_db.group.samplelist
            
            #for sample in this_db_samples:
            #    if sample not in self.samples:
            #        self.samples.append(sample)
            
            this_sample_data = this_trait.data
            print("this_sample_data", len(this_sample_data))
            
            #for sample in this_sample_data:
            #    if sample not in self.all_sample_list:
            #        self.all_sample_list.append(sample)
            
            corr_result_row = []
            for target in self.trait_list:
                target_trait = target[0]
                target_db = target[1]
                target_samples = target_db.group.samplelist
                
                if this_trait == target_trait and this_db == target_db:
                    corr_result_row.append(1)
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

                corr_result_row.append(sample_r)
                
            self.corr_results.append(corr_result_row)

        #self.sample_data = {}
        #for trait_db in self.trait_list:
        #    this_trait = trait_db[0]
        #
        #    this_sample_data = this_trait.data
        #    
        #    self.sample_data[this_trait.name] = []
        #    for sample in self.all_sample_list:
        #        if sample in this_sample_data:
        #            self.sample_data[this_trait.name].append(this_sample_data[sample].value)
        #        else:
        #            self.sample_data[this_trait.name].append('')

        print("corr_results:", pf(self.traits))

        groups = []
        for sample in self.all_sample_list:
            groups.append(1)

        self.js_data = dict(traits = self.traits,
                            groups = groups,
                            cols = range(len(self.traits)),
                            rows = range(len(self.traits)),
                            samples = self.all_sample_list,
                            sample_data = self.sample_data,
                            corr_results = self.corr_results,)
        
        
        
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

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
