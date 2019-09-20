from __future__ import absolute_import, print_function, division

import sys
# sys.path.append(".") Never in a running webserver

import string
import cPickle
import os
import datetime
import time
import pp
import math
import collections
import resource

import scipy
import numpy as np

from pprint import pformat as pf

import reaper

from base.trait import GeneralTrait
from base import data_set
from base import species
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data

from MySQLdb import escape_string as escape

import cPickle as pickle
import simplejson as json

from pprint import pformat as pf

from redis import Redis
Redis = Redis()

from flask import Flask, g

from utility.logger import getLogger
logger = getLogger(__name__ )

class Heatmap(object):

    def __init__(self, start_vars, temp_uuid):
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        helper_functions.get_trait_db_obs(self, trait_db_list)

        self.temp_uuid = temp_uuid
        self.num_permutations = 5000
        self.dataset = self.trait_list[0][1]

        self.json_data = {} #The dictionary that will be used to create the json object that contains all the data needed to create the figure

        self.all_sample_list = []
        self.traits = []

        chrnames = []
        self.species = species.TheSpecies(dataset=self.trait_list[0][1])
        for key in self.species.chromosomes.chromosomes.keys():
            chrnames.append([self.species.chromosomes.chromosomes[key].name, self.species.chromosomes.chromosomes[key].mb_length])

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

            this_trait_vals = []
            for sample in self.all_sample_list:
                if sample in this_sample_data:
                    this_trait_vals.append(this_sample_data[sample].value)
                else:
                    this_trait_vals.append('')
            self.sample_data.append(this_trait_vals)

        self.gen_reaper_results()

        lodnames = []
        chr_pos = []
        pos = []
        markernames = []

        for trait in self.trait_results.keys():
            lodnames.append(trait)

        self.dataset.group.get_markers()
        for marker in self.dataset.group.markers.markers:
            chr_pos.append(marker['chr'])
            pos.append(marker['Mb'])
            markernames.append(marker['name'])

        self.json_data['chrnames'] = chrnames
        self.json_data['lodnames'] = lodnames
        self.json_data['chr'] = chr_pos
        self.json_data['pos'] = pos
        self.json_data['markernames'] = markernames

        for trait in self.trait_results:
            self.json_data[trait] = self.trait_results[trait]

        self.js_data = dict(
            json_data = self.json_data
        )

    def gen_reaper_results(self):
        self.trait_results = {}
        for trait_db in self.trait_list:
            self.dataset.group.get_markers()
            this_trait = trait_db[0]
            #this_db = trait_db[1]
            genotype = self.dataset.group.read_genotype_file(use_reaper=True)
            samples, values, variances, sample_aliases = this_trait.export_informative()

            trimmed_samples = []
            trimmed_values = []
            for i in range(0, len(samples)):
                if samples[i] in self.dataset.group.samplelist:
                    trimmed_samples.append(str(samples[i]))
                    trimmed_values.append(values[i])

            reaper_results = genotype.regression(strains = trimmed_samples,
                                                 trait = trimmed_values)

            lrs_values = [float(qtl.lrs) for qtl in reaper_results]

            self.trait_results[this_trait.name] = []
            for qtl in reaper_results:
                if qtl.additive > 0:
                    self.trait_results[this_trait.name].append(-float(qtl.lrs))
                else:
                    self.trait_results[this_trait.name].append(float(qtl.lrs))
