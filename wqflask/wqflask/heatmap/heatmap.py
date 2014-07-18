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

class Heatmap(object):

    def __init__(self, start_vars):
    
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        
        helper_functions.get_trait_db_obs(self, trait_db_list)
        
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

        self.trait_results = {}
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]
            
            this_db_samples = this_db.group.samplelist
            this_sample_data = this_trait.data
            print("this_sample_data", this_sample_data)
                this_trait_vals = []
                for index, sample in enumerate(target_samples):
                    
                    if (sample in this_sample_data) and (sample in target_sample_data):
                        sample_value = this_sample_data[sample].value
                        target_sample_value = target_sample_data[sample].value
                        this_trait_vals.append(sample_value)
                        target_vals.append(target_sample_value)
            
            
            