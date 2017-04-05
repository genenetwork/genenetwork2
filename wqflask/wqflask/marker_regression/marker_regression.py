from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import math
import sys
import datetime
import os
import collections
import uuid

import rpy2.robjects as ro
import numpy as np
from scipy import linalg

import cPickle as pickle
import itertools

import simplejson as json

from redis import Redis
Redis = Redis()

from flask import Flask, g

from base.trait import GeneralTrait
from base import data_set
from base import species
from utility import webqtlUtil
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data
from utility.benchmark import Bench
from wqflask.marker_regression import gemma_mapping, rqtl_mapping, qtlreaper_mapping, plink_mapping

from utility.tools import locate, locate_ignore_error, PYLMM_COMMAND, GEMMA_COMMAND, GEMMA_RESULTS_PATH, PLINK_COMMAND, TEMPDIR
from utility.external import shell
from base.webqtlConfig import TMPDIR, GENERATED_TEXT_DIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

class MarkerRegression(object):

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

        self.mapping_method = start_vars['method']
        if start_vars['manhattan_plot'] == "True":
            self.manhattan_plot = True
        else:
            self.manhattan_plot = False

        self.maf = start_vars['maf'] # Minor allele frequency
        self.suggestive = ""
        self.significant = ""
        self.pair_scan = False # Initializing this since it is checked in views to determine which template to use
        self.score_type = "LRS" #ZS: LRS or LOD
        self.mapping_scale = "physic"
        self.num_perm = 0
        self.perm_output = []
        self.bootstrap_results = []

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

        self.dataset.group.get_markers()
        if self.mapping_method == "gemma":
            self.score_type = "-log(p)"
            self.manhattan_plot = True
            with Bench("Running GEMMA"):
                marker_obs = gemma_mapping.run_gemma(self.dataset, self.samples, self.vals)
            results = marker_obs
        elif self.mapping_method == "rqtl_plink":
            results = self.run_rqtl_plink()
        elif self.mapping_method == "rqtl_geno":
            self.score_type = "LOD"
            self.mapping_scale = "morgan"
            self.control_marker = start_vars['control_marker']
            self.do_control = start_vars['do_control']
            self.dataset.group.genofile = start_vars['genofile']
            self.method = start_vars['mapmethod_rqtl_geno']
            self.model = start_vars['mapmodel_rqtl_geno']
            if start_vars['pair_scan'] == "true":
                self.pair_scan = True
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
            self.dataset.group.genofile = start_vars['genofile']
            logger.info("Running qtlreaper")
            results, self.json_data, self.perm_output, self.suggestive, self.significant, self.bootstrap_results = qtlreaper_mapping.gen_reaper_results(self.this_trait,
                                                                                                                                                        self.dataset,
                                                                                                                                                        self.samples,
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
        elif self.mapping_method == "pylmm":
            logger.debug("RUNNING PYLMM")
            self.dataset.group.genofile = start_vars['genofile']
            if self.num_perm > 0:
                self.run_permutations(str(temp_uuid))
            results = self.gen_data(str(temp_uuid))
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
            self.cutoff = 2
            self.qtl_results = []
            highest_chr = 1 #This is needed in order to convert the highest chr to X/Y
            for marker in results:
                if marker['chr'] > 0 or marker['chr'] == "X" or marker['chr'] == "X/Y":
                    if marker['chr'] > highest_chr or marker['chr'] == "X" or marker['chr'] == "X/Y":
                        highest_chr = marker['chr']
                    if ('lod_score' in marker.keys()) or ('lrs_value' in marker.keys()):
                        self.qtl_results.append(marker)

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

                # logger.debug("json_data:", self.json_data)

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

    def run_permutations(self, temp_uuid):
        """Runs permutations and gets significant and suggestive LOD scores"""

        top_lod_scores = []

        #logger.debug("self.num_perm:", self.num_perm)

        for permutation in range(self.num_perm):

            pheno_vector = np.array([val == "x" and np.nan or float(val) for val in self.vals])
            np.random.shuffle(pheno_vector)

            key = "pylmm:input:" + temp_uuid

            if self.dataset.group.species == "human":
                p_values, t_stats = self.gen_human_results(pheno_vector, key, temp_uuid)
            else:
                genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]

                no_val_samples = self.identify_empty_samples()
                trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)

                genotype_matrix = np.array(trimmed_genotype_data).T

                params = dict(pheno_vector = pheno_vector.tolist(),
                            genotype_matrix = genotype_matrix.tolist(),
                            restricted_max_likelihood = True,
                            refit = False,
                            temp_uuid = temp_uuid,

                            # meta data
                            timestamp = datetime.datetime.now().isoformat(),
                            )

                json_params = json.dumps(params)
                Redis.set(key, json_params)
                Redis.expire(key, 60*60)

                command = PYLMM_COMMAND+' --key {} --species {}'.format(key,"other")
                shell(command)

                json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
                results = json.loads(json_results[1])
                p_values = [float(result) for result in results['p_values']]

                lowest_p_value = 1
                for p_value in p_values:
                    if p_value < lowest_p_value:
                        lowest_p_value = p_value

                #logger.debug("lowest_p_value:", lowest_p_value)
                top_lod_scores.append(-math.log10(lowest_p_value))

        #logger.debug("top_lod_scores:", top_lod_scores)

        self.suggestive = np.percentile(top_lod_scores, 67)
        self.significant = np.percentile(top_lod_scores, 95)

    def gen_data(self, temp_uuid):
        """Generates p-values for each marker"""

        logger.debug("self.vals is:", self.vals)
        pheno_vector = np.array([(val == "x" or val == "") and np.nan or float(val) for val in self.vals])

        #lmm_uuid = str(uuid.uuid4())

        key = "pylmm:input:" + temp_uuid
        logger.debug("key is:", pf(key))
        #with Bench("Loading cache"):
        #    result = Redis.get(key)

        if self.dataset.group.species == "human":
            p_values, t_stats = self.gen_human_results(pheno_vector, key, temp_uuid)
            #p_values = self.trim_results(p_values)

        else:
            logger.debug("NOW CWD IS:", os.getcwd())
            genotype_data = [marker['genotypes'] for marker in self.dataset.group.markers.markers]

            no_val_samples = self.identify_empty_samples()
            trimmed_genotype_data = self.trim_genotypes(genotype_data, no_val_samples)

            genotype_matrix = np.array(genotype_data).T

            #logger.debug("pheno_vector: ", pf(pheno_vector))
            #logger.debug("genotype_matrix: ", pf(genotype_matrix))
            #logger.debug("genotype_matrix.shape: ", pf(genotype_matrix.shape))

            #params = {"pheno_vector": pheno_vector,
            #            "genotype_matrix": genotype_matrix,
            #            "restricted_max_likelihood": True,
            #            "refit": False,
            #            "temp_data": tempdata}

            # logger.debug("genotype_matrix:", str(genotype_matrix.tolist()))
            # logger.debug("pheno_vector:", str(pheno_vector.tolist()))

            params = dict(pheno_vector = pheno_vector.tolist(),
                        genotype_matrix = genotype_matrix.tolist(),
                        restricted_max_likelihood = True,
                        refit = False,
                        temp_uuid = temp_uuid,

                        # meta data
                        timestamp = datetime.datetime.now().isoformat(),
                        )

            json_params = json.dumps(params)
            #logger.debug("json_params:", json_params)
            Redis.set(key, json_params)
            Redis.expire(key, 60*60)
            logger.debug("before printing command")

            command = PYLMM_COMMAND + ' --key {} --species {}'.format(key, "other")
            logger.debug("command is:", command)
            logger.debug("after printing command")

            shell(command)

            #t_stats, p_values = lmm.run(key)
            #lmm.run(key)

            json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
            results = json.loads(json_results[1])
            p_values = [float(result) for result in results['p_values']]
            #logger.debug("p_values:", p_values[:10])
            #p_values = self.trim_results(p_values)
            t_stats = results['t_stats']

            #t_stats, p_values = lmm.run(
            #    pheno_vector,
            #    genotype_matrix,
            #    restricted_max_likelihood=True,
            #    refit=False,
            #    temp_data=tempdata
            #)
            #logger.debug("p_values:", p_values)

        self.dataset.group.markers.add_pvalues(p_values)

        #self.get_lod_score_cutoff()

        return self.dataset.group.markers.markers

    def trim_results(self, p_values):
        logger.debug("len_p_values:", len(p_values))
        if len(p_values) > 500:
            p_values.sort(reverse=True)
            trimmed_values = p_values[:500]

        return trimmed_values

    #def gen_human_results(self, pheno_vector, tempdata):
    def gen_human_results(self, pheno_vector, key, temp_uuid):
        file_base = locate(self.dataset.group.name,"mapping")

        plink_input = input.plink(file_base, type='b')
        input_file_name = os.path.join(webqtlConfig.SNP_PATH, self.dataset.group.name + ".snps.gz")

        pheno_vector = pheno_vector.reshape((len(pheno_vector), 1))
        covariate_matrix = np.ones((pheno_vector.shape[0],1))
        kinship_matrix = np.fromfile(open(file_base + '.kin','r'),sep=" ")
        kinship_matrix.resize((len(plink_input.indivs),len(plink_input.indivs)))

        logger.debug("Before creating params")

        params = dict(pheno_vector = pheno_vector.tolist(),
                    covariate_matrix = covariate_matrix.tolist(),
                    input_file_name = input_file_name,
                    kinship_matrix = kinship_matrix.tolist(),
                    refit = False,
                    temp_uuid = temp_uuid,

                    # meta data
                    timestamp = datetime.datetime.now().isoformat(),
                    )

        logger.debug("After creating params")

        json_params = json.dumps(params)
        Redis.set(key, json_params)
        Redis.expire(key, 60*60)

        logger.debug("Before creating the command")

        command = PYLMM_COMMAND+' --key {} --species {}'.format(key, "human")

        logger.debug("command is:", command)

        os.system(command)

        json_results = Redis.blpop("pylmm:results:" + temp_uuid, 45*60)
        results = json.loads(json_results[1])
        t_stats = results['t_stats']
        p_values = results['p_values']


        #p_values, t_stats = lmm.run_human(key)

        #p_values, t_stats = lmm.run_human(
        #        pheno_vector,
        #        covariate_matrix,
        #        input_file_name,
        #        kinship_matrix,
        #        loading_progress=tempdata
        #    )

        return p_values, t_stats

    def get_lod_score_cutoff(self):
        logger.debug("INSIDE GET LOD CUTOFF")
        high_qtl_count = 0
        for marker in self.dataset.group.markers.markers:
            if marker['lod_score'] > 1:
                high_qtl_count += 1

        if high_qtl_count > 1000:
            return 1
        else:
            return 0

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
    """
    This function is only called by main below
    """
    raise Exception("Paths are undefined here")
    plink_file_base = os.path.join(TMPDIR, group)
    plink_input = input.plink(plink_file_base, type='b')

    data = dict(plink_input = list(plink_input),
                numSNPs = plink_input.numSNPs)

    #input_dict = {}
    #
    #input_dict['plink_input'] = list(plink_input)
    #input_dict['numSNPs'] = plink_input.numSNPs
    #

    snp_file_base = os.path.join(webqtlConfig.SNP_PATH, group + ".snps.gz")

    with gzip.open(snp_file_base, "wb") as fh:
        pickle.dump(data, fh, pickle.HIGHEST_PROTOCOL)

def trim_markers_for_table(markers):
    num_markers = len(markers)

    if 'lod_score' in markers[0].keys():
        sorted_markers = sorted(markers, key=lambda k: k['lod_score'], reverse=True)
    else:
        sorted_markers = sorted(markers, key=lambda k: k['lrs_value'], reverse=True)

    #ZS: So we end up with a list of just 200 markers
    if len(sorted_markers) >= 200:
        trimmed_sorted_markers = sorted_markers[:200]
        return trimmed_sorted_markers
    else:
        return sorted_markers


if __name__ == '__main__':
    import cPickle as pickle
