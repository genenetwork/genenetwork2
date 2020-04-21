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
import random
import collections
import resource

import scipy
import numpy as np

from pprint import pformat as pf

import reaper

from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data
from utility.tools import flat_files, REAPER_COMMAND, TEMPDIR

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

            genotype = self.dataset.group.read_genotype_file(use_reaper=False)
            samples, values, variances, sample_aliases = this_trait.export_informative()

            if self.dataset.group.genofile != None:
                genofile_name = self.dataset.group.genofile[:-5]
            else:
                genofile_name = self.dataset.group.name

            trimmed_samples = []
            trimmed_values = []
            for i in range(0, len(samples)):
                if samples[i] in self.dataset.group.samplelist:
                    trimmed_samples.append(str(samples[i]))
                    trimmed_values.append(values[i])

            trait_filename = str(this_trait.name) + "_" + str(self.dataset.name) + "_pheno"
            gen_pheno_txt_file(trimmed_samples, trimmed_values, trait_filename)

            output_filename = self.dataset.group.name + "_GWA_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

            reaper_command = REAPER_COMMAND + ' --geno {0}/{1}.geno --traits {2}/gn2/{3}.txt -n 1000 -o {4}{5}.txt'.format(flat_files('genotype'),
                                                                                                                    genofile_name,
                                                                                                                    TEMPDIR,
                                                                                                                    trait_filename,
                                                                                                                    webqtlConfig.GENERATED_IMAGE_DIR,
                                                                                                                    output_filename)

            os.system(reaper_command)                                                                                                        

            reaper_results = parse_reaper_output(output_filename)

            lrs_values = [float(qtl['lrs_value']) for qtl in reaper_results]

            self.trait_results[this_trait.name] = []
            for qtl in reaper_results:
                if qtl['additive'] > 0:
                    self.trait_results[this_trait.name].append(-float(qtl['lrs_value']))
                else:
                    self.trait_results[this_trait.name].append(float(qtl['lrs_value']))

def gen_pheno_txt_file(samples, vals, filename):
    """Generates phenotype file for GEMMA"""

    with open("{0}/gn2/{1}.txt".format(TEMPDIR, filename), "w") as outfile:
        outfile.write("Trait\t")

        filtered_sample_list = []
        filtered_vals_list = []
        for i, sample in enumerate(samples):
            if vals[i] != "x":
                filtered_sample_list.append(sample)
                filtered_vals_list.append(str(vals[i]))

        samples_string = "\t".join(filtered_sample_list)
        outfile.write(samples_string + "\n")
        outfile.write("T1\t")
        values_string = "\t".join(filtered_vals_list)
        outfile.write(values_string)

def parse_reaper_output(gwa_filename):
    included_markers = []
    p_values = []
    marker_obs = []

    with open("{}{}.txt".format(webqtlConfig.GENERATED_IMAGE_DIR, gwa_filename)) as output_file:
        for line in output_file:
            if line.startswith("ID\t"):
                continue
            else:
                marker = {}
                marker['name'] = line.split("\t")[1]
                try:
                    marker['chr'] = int(line.split("\t")[2])
                except:
                    marker['chr'] = line.split("\t")[2]
                marker['cM'] = float(line.split("\t")[3])
                marker['Mb'] = float(line.split("\t")[4])
                if float(line.split("\t")[7]) != 1:
                    marker['p_value'] = float(line.split("\t")[7])
                marker['lrs_value'] = float(line.split("\t")[5])
                marker['lod_score'] = marker['lrs_value'] / 4.61
                marker['additive'] = float(line.split("\t")[6])
                marker_obs.append(marker)

    return marker_obs