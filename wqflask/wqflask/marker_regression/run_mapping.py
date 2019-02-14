from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import math
import random
import sys
import datetime
import os
import collections
import uuid

import rpy2.robjects as ro
import numpy as np

import cPickle as pickle
import itertools

import simplejson as json

from redis import Redis
Redis = Redis()

from flask import Flask, g

from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from utility import webqtlUtil
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data
from utility.benchmark import Bench
from wqflask.marker_regression import gemma_mapping, rqtl_mapping, qtlreaper_mapping, plink_mapping

from utility.tools import locate, locate_ignore_error, GEMMA_COMMAND, PLINK_COMMAND, TEMPDIR
from utility.external import shell
from base.webqtlConfig import TMPDIR, GENERATED_TEXT_DIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

class RunMapping(object):

    def __init__(self, start_vars, temp_uuid):

        helper_functions.get_species_dataset_trait(self, start_vars)

        self.temp_uuid = temp_uuid #needed to pass temp_uuid to gn1 mapping code (marker_regression_gn1.py)

        self.json_data = {}
        self.json_data['lodnames'] = ['lod.hk']

        self.samples = [] # Want only ones with values
        self.vals = []

        all_samples_ordered = self.dataset.group.all_samples_ordered()
        primary_sample_names = list(all_samples_ordered)

        for sample in self.dataset.group.samplelist:
            # sample is actually the name of an individual
            in_trait_data = False
            for item in self.this_trait.data:
                if self.this_trait.data[item].name == sample:
                    value = start_vars['value:' + self.this_trait.data[item].name]
                    self.samples.append(self.this_trait.data[item].name)
                    self.vals.append(value)
                    in_trait_data = True
                    break
            if not in_trait_data:
                value = start_vars.get('value:' + sample)
                if value:
                    self.samples.append(sample)
                    self.vals.append(value)

        #ZS: Check if genotypes exist in the DB in order to create links for markers
        if "geno_db_exists" in start_vars:
            self.geno_db_exists = start_vars['geno_db_exists']
        else:
          try:
            self.geno_db_exists = "True"
          except:
            self.geno_db_exists = "False"

        self.mapping_method = start_vars['method']
        if "results_path" in start_vars:
            self.mapping_results_path = start_vars['results_path']
        else:
            mapping_results_filename = self.dataset.group.name + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.mapping_results_path = "{}{}.csv".format(webqtlConfig.GENERATED_IMAGE_DIR, mapping_results_filename)

        if start_vars['manhattan_plot'] == "True":
            self.manhattan_plot = True
        else:
            self.manhattan_plot = False

        self.maf = start_vars['maf'] # Minor allele frequency
        if "use_loco" in start_vars:
            self.use_loco = start_vars['use_loco']
        else:
            self.use_loco = None
        self.suggestive = ""
        self.significant = ""
        self.pair_scan = False # Initializing this since it is checked in views to determine which template to use
        self.score_type = "LRS" #ZS: LRS or LOD
        self.mapping_scale = "physic"
        self.num_perm = 0
        self.perm_output = []
        self.bootstrap_results = []
        self.covariates = start_vars['covariates'] if "covariates" in start_vars else None

        #ZS: This is passed to GN1 code for single chr mapping
        self.selected_chr = -1
        if "selected_chr" in start_vars:
            if int(start_vars['selected_chr']) != -1: #ZS: Needs to be -1 if showing full map; there's probably a better way to fix this
                self.selected_chr = int(start_vars['selected_chr']) + 1
            else:
                self.selected_chr = int(start_vars['selected_chr'])
        if "startMb" in start_vars:
            self.startMb = start_vars['startMb']
        if "endMb" in start_vars:
            self.endMb = start_vars['endMb']
        if "graphWidth" in start_vars:
            self.graphWidth = start_vars['graphWidth']
        if "lrsMax" in start_vars:
            self.lrsMax = start_vars['lrsMax']
        if "haplotypeAnalystCheck" in start_vars:
            self.haplotypeAnalystCheck = start_vars['haplotypeAnalystCheck']
        if "startMb" in start_vars: #ZS: This is to ensure showGenes, Legend, etc are checked the first time you open the mapping page, since startMb will only not be set during the first load
            if "permCheck" in start_vars:
                self.permCheck = "ON"
            else:
                self.permCheck = False
            self.num_perm = int(start_vars['num_perm'])

            self.LRSCheck = start_vars['LRSCheck']

            if "showSNP" in start_vars:
                self.showSNP = start_vars['showSNP']
            else:
                self.showSNP = False

            if "showGenes" in start_vars:
                self.showGenes = start_vars['showGenes']
            else:
                self.showGenes = False

            if "viewLegend" in start_vars:
                self.viewLegend = start_vars['viewLegend']
            else:
                self.viewLegend = False
        else:
            try:
                if int(start_vars['num_perm']) > 0:
                    self.num_perm = int(start_vars['num_perm'])
            except:
                self.num_perm = 0

            if self.num_perm > 0:
                self.permCheck = "ON"
            else:
                self.permCheck = False
            self.showSNP = "ON"
            self.showGenes = "ON"
            self.viewLegend = "ON"

        if 'genofile' in start_vars:
          if start_vars['genofile'] != "":
            self.genofile_string = start_vars['genofile']
            self.dataset.group.genofile = self.genofile_string.split(":")[0]
        self.dataset.group.get_markers()
        if self.mapping_method == "gemma":
            self.score_type = "-log(p)"
            self.manhattan_plot = True
            with Bench("Running GEMMA"):
                marker_obs = gemma_mapping.run_gemma(self.this_trait, self.dataset, self.samples, self.vals, self.covariates, self.use_loco, self.maf)
            results = marker_obs
        elif self.mapping_method == "rqtl_plink":
            results = self.run_rqtl_plink()
        elif self.mapping_method == "rqtl_geno":
            self.score_type = "LOD"
            self.mapping_scale = "morgan"
            self.control_marker = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            self.method = start_vars['mapmethod_rqtl_geno']
            self.model = start_vars['mapmodel_rqtl_geno']
            #if start_vars['pair_scan'] == "true":
            #    self.pair_scan = True
            if self.permCheck and self.num_perm > 0:
                self.perm_output, self.suggestive, self.significant, results = rqtl_mapping.run_rqtl_geno(self.vals, self.dataset, self.method, self.model, self.permCheck, self.num_perm, self.do_control, self.control_marker, self.manhattan_plot, self.pair_scan)
            else:
                results = rqtl_mapping.run_rqtl_geno(self.vals, self.dataset, self.method, self.model, self.permCheck, self.num_perm, self.do_control, self.control_marker, self.manhattan_plot, self.pair_scan)
        elif self.mapping_method == "reaper":
            if "startMb" in start_vars: #ZS: Check if first time page loaded, so it can default to ON
                if "additiveCheck" in start_vars:
                    self.additiveCheck = start_vars['additiveCheck']
                else:
                    self.additiveCheck = False

                if "bootCheck" in start_vars:
                    self.bootCheck = "ON"
                else:
                    self.bootCheck = False
                self.num_bootstrap = int(start_vars['num_bootstrap'])
            else:
                self.additiveCheck = "ON"
                try:
                    if int(start_vars['num_bootstrap']) > 0:
                        self.bootCheck = "ON"
                        self.num_bootstrap = int(start_vars['num_bootstrap'])
                    else:
                        self.bootCheck = False
                        self.num_bootstrap = 0
                except:
                    self.bootCheck = False
                    self.num_bootstrap = 0

            self.control_marker = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            logger.info("Running qtlreaper")
            results, self.json_data, self.perm_output, self.suggestive, self.significant, self.bootstrap_results = qtlreaper_mapping.gen_reaper_results(self.this_trait,
                                                                                                                                                        self.dataset,
                                                                                                                                                        self.samples,
                                                                                                                                                        self.vals,
                                                                                                                                                        self.json_data,
                                                                                                                                                        self.num_perm,
                                                                                                                                                        self.bootCheck,
                                                                                                                                                        self.num_bootstrap,
                                                                                                                                                        self.do_control,
                                                                                                                                                        self.control_marker,
                                                                                                                                                        self.manhattan_plot)
        elif self.mapping_method == "plink":
            self.score_type = "-log(p)"
            self.manhattan_plot = True
            results = plink_mapping.run_plink(self.this_trait, self.dataset, self.species, self.vals, self.maf)
            #results = self.run_plink()
        else:
            logger.debug("RUNNING NOTHING")

        if self.pair_scan == True:
            self.qtl_results = []
            highest_chr = 1 #This is needed in order to convert the highest chr to X/Y
            for marker in results:
                if marker['chr1'] > 0 or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                    if marker['chr1'] > highest_chr or marker['chr1'] == "X" or marker['chr1'] == "X/Y":
                        highest_chr = marker['chr1']
                    if 'lod_score' in marker.keys():
                        self.qtl_results.append(marker)

            self.trimmed_markers = results

            for qtl in enumerate(self.qtl_results):
                self.json_data['chr1'].append(str(qtl['chr1']))
                self.json_data['chr2'].append(str(qtl['chr2']))
                self.json_data['Mb'].append(qtl['Mb'])
                self.json_data['markernames'].append(qtl['name'])

            self.js_data = dict(
                json_data = self.json_data,
                this_trait = self.this_trait.name,
                data_set = self.dataset.name,
                maf = self.maf,
                manhattan_plot = self.manhattan_plot,
                mapping_scale = self.mapping_scale,
                qtl_results = self.qtl_results
            )

        else:
            self.qtl_results = []
            highest_chr = 1 #This is needed in order to convert the highest chr to X/Y
            for marker in results:
                if marker['chr'] > 0 or marker['chr'] == "X" or marker['chr'] == "X/Y":
                    if marker['chr'] > highest_chr or marker['chr'] == "X" or marker['chr'] == "X/Y":
                        highest_chr = marker['chr']
                    if ('lod_score' in marker.keys()) or ('lrs_value' in marker.keys()):
                        self.qtl_results.append(marker)

            with Bench("Exporting Results"):
                export_mapping_results(self.dataset, self.this_trait, self.qtl_results, self.mapping_results_path, self.mapping_scale, self.score_type)

            with Bench("Trimming Markers for Figure"):
                if len(self.qtl_results) > 30000:
                    self.qtl_results = trim_markers_for_figure(self.qtl_results)

            with Bench("Trimming Markers for Table"):
                self.trimmed_markers = trim_markers_for_table(results)

            if self.mapping_method != "gemma":
                self.json_data['chr'] = []
                self.json_data['pos'] = []
                self.json_data['lod.hk'] = []
                self.json_data['markernames'] = []

                self.json_data['suggestive'] = self.suggestive
                self.json_data['significant'] = self.significant

                #Need to convert the QTL objects that qtl reaper returns into a json serializable dictionary
                for index, qtl in enumerate(self.qtl_results):
                    #if index<40:
                    #    logger.debug("lod score is:", qtl['lod_score'])
                    if qtl['chr'] == highest_chr and highest_chr != "X" and highest_chr != "X/Y":
                        #logger.debug("changing to X")
                        self.json_data['chr'].append("X")
                    else:
                        self.json_data['chr'].append(str(qtl['chr']))
                    self.json_data['pos'].append(qtl['Mb'])
                    if 'lrs_value' in qtl.keys():
                        self.json_data['lod.hk'].append(str(qtl['lrs_value']))
                    else:
                        self.json_data['lod.hk'].append(str(qtl['lod_score']))
                    self.json_data['markernames'].append(qtl['name'])

                #Get chromosome lengths for drawing the interval map plot
                chromosome_mb_lengths = {}
                self.json_data['chrnames'] = []
                for key in self.species.chromosomes.chromosomes.keys():
                    self.json_data['chrnames'].append([self.species.chromosomes.chromosomes[key].name, self.species.chromosomes.chromosomes[key].mb_length])
                    chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length

                self.js_data = dict(
                    result_score_type = self.score_type,
                    json_data = self.json_data,
                    this_trait = self.this_trait.name,
                    data_set = self.dataset.name,
                    maf = self.maf,
                    manhattan_plot = self.manhattan_plot,
                    mapping_scale = self.mapping_scale,
                    chromosomes = chromosome_mb_lengths,
                    qtl_results = self.qtl_results,
                    num_perm = self.num_perm,
                    perm_results = self.perm_output,
                )

    def run_rqtl_plink(self):
        # os.chdir("") never do this inside a webserver!!

        output_filename = webqtlUtil.genRandStr("%s_%s_"%(self.dataset.group.name, self.this_trait.name))

        plink_mapping.gen_pheno_txt_file_plink(self.this_trait, self.dataset, self.vals, pheno_filename = output_filename)

        rqtl_command = './plink --noweb --ped %s.ped --no-fid --no-parents --no-sex --no-pheno --map %s.map --pheno %s/%s.txt --pheno-name %s --maf %s --missing-phenotype -9999 --out %s%s --assoc ' % (self.dataset.group.name, self.dataset.group.name, TMPDIR, plink_output_filename, self.this_trait.name, self.maf, TMPDIR, plink_output_filename)

        os.system(rqtl_command)

        count, p_values = self.parse_rqtl_output(plink_output_filename)

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

def export_mapping_results(dataset, trait, markers, results_path, mapping_scale, score_type):
    with open(results_path, "w+") as output_file:
        output_file.write("Population: " + dataset.group.species.title() + " " + dataset.group.name + "\n")
        output_file.write("Data Set: " + dataset.fullname + "\n")
        if dataset.type == "ProbeSet":
            output_file.write("Gene Symbol: " + trait.symbol + "\n")
            output_file.write("Location: " + str(trait.chr) + " @ " + str(trait.mb) + " Mb\n")
        output_file.write("\n")
        output_file.write("Name,Chr,")
        if mapping_scale == "physic":
            output_file.write("Mb," + score_type)
        else:
            output_file.write("Cm," + score_type)
        if "additive" in markers[0].keys():
            output_file.write(",Additive")
        if "dominance" in markers[0].keys():
            output_file.write(",Dominance")
        output_file.write("\n")
        for i, marker in enumerate(markers):
            output_file.write(marker['name'] + "," + str(marker['chr']) + "," + str(marker['Mb']) + ",")
            if "lod_score" in marker.keys():
                output_file.write(str(marker['lod_score']))
            else:
                output_file.write(str(marker['lrs_value']))
            if "additive" in marker.keys():
                output_file.write("," + str(marker['additive']))
            if "dominance" in marker.keys():
                output_file.write("," + str(marker['dominance']))
            if i < (len(markers) - 1):
                output_file.write("\n")

def trim_markers_for_figure(markers):
    if 'lod_score' in markers[0].keys():
        score_type = 'lod_score'
    else:
        score_type = 'lrs_value'

    filtered_markers = []
    low_counter = 0
    med_counter = 0
    high_counter = 0
    for marker in markers:
        if score_type == 'lod_score':
            if marker[score_type] < 1:
                if low_counter % 20 == 0:
                    filtered_markers.append(marker)
                low_counter += 1
            elif 1 <= marker[score_type] < 2:
                if med_counter % 10 == 0:
                    filtered_markers.append(marker)
                med_counter += 1
            elif 2 <= marker[score_type] <= 3:
                if high_counter % 2 == 0:
                    filtered_markers.append(marker)
                high_counter += 1
            else:
                filtered_markers.append(marker)
        else:
            if marker[score_type] < 4.16:
                if low_counter % 20 == 0:
                    filtered_markers.append(marker)
                low_counter += 1
            elif 4.16 <= marker[score_type] < (2*4.16):
                if med_counter % 10 == 0:
                    filtered_markers.append(marker)
                med_counter += 1
            elif (2*4.16) <= marker[score_type] <= (3*4.16):
                if high_counter % 2 == 0:
                    filtered_markers.append(marker)
                high_counter += 1
            else:
                filtered_markers.append(marker)
    return filtered_markers

def trim_markers_for_table(markers):
    if 'lod_score' in markers[0].keys():
        sorted_markers = sorted(markers, key=lambda k: k['lod_score'], reverse=True)
    else:
        sorted_markers = sorted(markers, key=lambda k: k['lrs_value'], reverse=True)

    #ZS: So we end up with a list of just 2000 markers
    if len(sorted_markers) >= 2000:
        trimmed_sorted_markers = sorted_markers[:2000]
        return trimmed_sorted_markers
    else:
        return sorted_markers
