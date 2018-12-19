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
# sys.path.append(".")   Never do this in a webserver!

import string
import cPickle
import os
import time
import pp
import math
import collections
import resource


from pprint import pformat as pf

from htmlgen import HTMLgen2 as HT
import reaper

from base.trait import GeneralTrait
from base import data_set
from utility import webqtlUtil, helper_functions, corr_result_helpers
from db import webqtlDatabaseFunction
import utility.webqtlUtil #this is for parallel computing only.
from wqflask.correlation import correlation_functions
from utility.benchmark import Bench

from MySQLdb import escape_string as escape

from pprint import pformat as pf

from flask import Flask, g


class ComparisonBarChart(object):

    def __init__(self, start_vars):
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]

        helper_functions.get_trait_db_obs(self, trait_db_list)

        self.all_sample_list = []
        self.traits = []
        self.insufficient_shared_samples = False
        this_group = self.trait_list[0][1].group.name #ZS: Getting initial group name before verifying all traits are in the same group in the following loop
        for trait_db in self.trait_list:
            
            if trait_db[1].group.name != this_group:
                self.insufficient_shared_samples = True
                break
            else:
                this_group = trait_db[1].group.name
            this_trait = trait_db[0]
            self.traits.append(this_trait)
            
            this_sample_data = this_trait.data

            for sample in this_sample_data:
                if sample not in self.all_sample_list:
                    self.all_sample_list.append(sample)

        if self.insufficient_shared_samples:
            pass
        else:
            self.sample_data = []
            for trait_db in self.trait_list:
                this_trait = trait_db[0]
                this_sample_data = this_trait.data

                this_trait_vals = []
                for sample in self.all_sample_list:
                    if sample in this_sample_data:
                        this_trait_vals.append(this_sample_data[sample].value)
                    else:
                        this_trait_vals.append('')
                self.sample_data.append(this_trait_vals)

            self.js_data = dict(traits = [trait.name for trait in self.traits],
                                samples = self.all_sample_list,
                                sample_data = self.sample_data,)
        
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

