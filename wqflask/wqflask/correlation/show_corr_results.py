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

import string
import cPickle
import os
import time
import pp
import math
import collections
import resource
import json

import scipy
import numpy

from pprint import pformat as pf

import reaper

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.trait import GeneralTrait
from base import data_set
from utility import webqtlUtil, helper_functions, corr_result_helpers
from db import webqtlDatabaseFunction
import utility.webqtlUtil #this is for parallel computing only.
from wqflask.correlation import correlation_functions
from utility.benchmark import Bench
import utility.webqtlUtil
from utility.type_checking import is_float, is_int, is_str, get_float, get_int, get_string
from wqflask import user_manager

from MySQLdb import escape_string as escape

from pprint import pformat as pf

from flask import Flask, g

import utility.logger
logger = utility.logger.getLogger(__name__ )

METHOD_LIT = "3"
METHOD_TISSUE_PEARSON = "4"
METHOD_TISSUE_RANK = "5"

TISSUE_METHODS = [METHOD_TISSUE_PEARSON, METHOD_TISSUE_RANK]

TISSUE_MOUSE_DB = 1

class CorrelationResults(object):
    def __init__(self, start_vars):
        # get trait list from db (database name)
        # calculate correlation with Base vector and targets

        # Check parameters
        assert('corr_type' in start_vars)
        assert(is_str(start_vars['corr_type']))
        assert('dataset' in start_vars)
        # assert('group' in start_vars) permitted to be empty?
        assert('corr_sample_method' in start_vars)
        assert('corr_samples_group' in start_vars)
        assert('corr_dataset' in start_vars)
        #assert('min_expr' in start_vars)
        assert('corr_return_results' in start_vars)
        if 'loc_chr' in start_vars:
            assert('min_loc_mb' in start_vars)
            assert('max_loc_mb' in start_vars)

        with Bench("Doing correlations"):
            if start_vars['dataset'] == "Temp":
                self.dataset = data_set.create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = start_vars['group'])
                self.trait_id = start_vars['trait_id']
                self.this_trait = GeneralTrait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)
            else:
                helper_functions.get_species_dataset_trait(self, start_vars)

            #self.dataset.group.read_genotype_file()

            corr_samples_group = start_vars['corr_samples_group']

            self.sample_data = {}
            self.corr_type = start_vars['corr_type']
            self.corr_method = start_vars['corr_sample_method']
            self.min_expr = get_float(start_vars,'min_expr')
            self.p_range_lower = get_float(start_vars,'p_range_lower',-1.0)
            self.p_range_upper = get_float(start_vars,'p_range_upper',1.0)

            if ('loc_chr' in start_vars and
                'min_loc_mb' in start_vars and
                'max_loc_mb' in start_vars):

                self.location_chr = get_string(start_vars,'loc_chr')
                self.min_location_mb = get_int(start_vars,'min_loc_mb')
                self.max_location_mb = get_int(start_vars,'max_loc_mb')
            else:
                self.location_chr = self.min_location_mb = self.max_location_mb = None

            self.get_formatted_corr_type()
            self.return_number = int(start_vars['corr_return_results'])

            #The two if statements below append samples to the sample list based upon whether the user
            #rselected Primary Samples Only, Other Samples Only, or All Samples

            primary_samples = self.dataset.group.samplelist
            if self.dataset.group.parlist != None:
                primary_samples += self.dataset.group.parlist
            if self.dataset.group.f1list != None:
                primary_samples += self.dataset.group.f1list

            #If either BXD/whatever Only or All Samples, append all of that group's samplelist
            if corr_samples_group != 'samples_other':
                self.process_samples(start_vars, primary_samples)

            #If either Non-BXD/whatever or All Samples, get all samples from this_trait.data and
            #exclude the primary samples (because they would have been added in the previous
            #if statement if the user selected All Samples)
            if corr_samples_group != 'samples_primary':
                if corr_samples_group == 'samples_other':
                    primary_samples = [x for x in primary_samples if x not in (
                                    self.dataset.group.parlist + self.dataset.group.f1list)]
                self.process_samples(start_vars, self.this_trait.data.keys(), primary_samples)

            self.target_dataset = data_set.create_dataset(start_vars['corr_dataset'])
            self.target_dataset.get_trait_data(self.sample_data.keys())

            self.header_fields = get_header_fields(self.target_dataset.type, self.corr_method)

            if self.target_dataset.type == "ProbeSet":
                self.filter_cols = [7, 6]
            elif self.target_dataset.type == "Publish":
                self.filter_cols = [6, 0]
            else:
                self.filter_cols = [4, 0]

            self.correlation_results = []

            self.correlation_data = {}

            if self.corr_type == "tissue":
                self.trait_symbol_dict = self.dataset.retrieve_genes("Symbol")

                tissue_corr_data = self.do_tissue_correlation_for_all_traits()
                if tissue_corr_data != None:
                    for trait in tissue_corr_data.keys()[:self.return_number]:
                        self.get_sample_r_and_p_values(trait, self.target_dataset.trait_data[trait])
                else:
                    for trait, values in self.target_dataset.trait_data.iteritems():
                        self.get_sample_r_and_p_values(trait, values)

            elif self.corr_type == "lit":
                self.trait_geneid_dict = self.dataset.retrieve_genes("GeneId")
                lit_corr_data = self.do_lit_correlation_for_all_traits()

                for trait in lit_corr_data.keys()[:self.return_number]:
                    self.get_sample_r_and_p_values(trait, self.target_dataset.trait_data[trait])

            elif self.corr_type == "sample":
                for trait, values in self.target_dataset.trait_data.iteritems():
                    self.get_sample_r_and_p_values(trait, values)

            self.correlation_data = collections.OrderedDict(sorted(self.correlation_data.items(),
                                                                   key=lambda t: -abs(t[1][0])))

            if self.target_dataset.type == "ProbeSet" or self.target_dataset.type == "Geno":
                #ZS: Convert min/max chromosome to an int for the location range option
                range_chr_as_int = None
                for order_id, chr_info in self.dataset.species.chromosomes.chromosomes.iteritems():
                    if 'loc_chr' in start_vars:
                        if chr_info.name == self.location_chr:
                            range_chr_as_int = order_id

            for _trait_counter, trait in enumerate(self.correlation_data.keys()[:self.return_number]):
                trait_object = GeneralTrait(dataset=self.target_dataset, name=trait, get_qtl_info=True, get_sample_info=False)

                if self.target_dataset.type == "ProbeSet" or self.target_dataset.type == "Geno":
                    #ZS: Convert trait chromosome to an int for the location range option
                    chr_as_int = 0
                    for order_id, chr_info in self.dataset.species.chromosomes.chromosomes.iteritems():
                        if chr_info.name == trait_object.chr:
                            chr_as_int = order_id

                if (float(self.correlation_data[trait][0]) >= self.p_range_lower and
                    float(self.correlation_data[trait][0]) <= self.p_range_upper):

                    if self.target_dataset.type == "ProbeSet" or self.target_dataset.type == "Geno":

                        if (self.min_expr != None) and (float(trait_object.mean) < self.min_expr):
                            continue
                        elif range_chr_as_int != None and (chr_as_int != range_chr_as_int):
                            continue
                        elif (self.min_location_mb != None) and (float(trait_object.mb) < float(self.min_location_mb)):
                            continue
                        elif (self.max_location_mb != None) and (float(trait_object.mb) > float(self.max_location_mb)):
                            continue

                    (trait_object.sample_r,
                    trait_object.sample_p,
                    trait_object.num_overlap) = self.correlation_data[trait]

                    # Set some sane defaults
                    trait_object.tissue_corr = 0
                    trait_object.tissue_pvalue = 0
                    trait_object.lit_corr = 0
                    if self.corr_type == "tissue" and tissue_corr_data != None:
                        trait_object.tissue_corr = tissue_corr_data[trait][1]
                        trait_object.tissue_pvalue = tissue_corr_data[trait][2]
                    elif self.corr_type == "lit":
                        trait_object.lit_corr = lit_corr_data[trait][1]
                    self.correlation_results.append(trait_object)

            self.target_dataset.get_trait_info(self.correlation_results, self.target_dataset.group.species)

            if self.corr_type != "lit" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
                self.do_lit_correlation_for_trait_list()

            if self.corr_type != "tissue" and self.dataset.type == "ProbeSet" and self.target_dataset.type == "ProbeSet":
                self.do_tissue_correlation_for_trait_list()

        self.json_results = generate_corr_json(self.correlation_results, self.this_trait, self.dataset, self.target_dataset)

############################################################################################################################################

    def get_formatted_corr_type(self):
        self.formatted_corr_type = ""
        if self.corr_type == "lit":
            self.formatted_corr_type += "Literature Correlation "
        elif self.corr_type == "tissue":
            self.formatted_corr_type += "Tissue Correlation "
        elif self.corr_type == "sample":
            self.formatted_corr_type += "Genetic Correlation "

        if self.corr_method == "pearson":
            self.formatted_corr_type += "(Pearson's r)"
        elif self.corr_method == "spearman":
            self.formatted_corr_type += "(Spearman's rho)"

    def do_tissue_correlation_for_trait_list(self, tissue_dataset_id=1):
        """Given a list of correlation results (self.correlation_results), gets the tissue correlation value for each"""

        #Gets tissue expression values for the primary trait
        primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list = [self.this_trait.symbol])

        if self.this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
            primary_trait_tissue_values = primary_trait_tissue_vals_dict[self.this_trait.symbol.lower()]
            gene_symbol_list = [trait.symbol for trait in self.correlation_results if trait.symbol]

            corr_result_tissue_vals_dict= correlation_functions.get_trait_symbol_and_tissue_values(
                                                    symbol_list=gene_symbol_list)

            for trait in self.correlation_results:
                if trait.symbol and trait.symbol.lower() in corr_result_tissue_vals_dict:
                    this_trait_tissue_values = corr_result_tissue_vals_dict[trait.symbol.lower()]

                    result = correlation_functions.cal_zero_order_corr_for_tiss(primary_trait_tissue_values,
                                                                          this_trait_tissue_values,
                                                                          self.corr_method)

                    trait.tissue_corr = result[0]
                    trait.tissue_pvalue = result[2]

    def do_tissue_correlation_for_all_traits(self, tissue_dataset_id=1):
        #Gets tissue expression values for the primary trait
        primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list = [self.this_trait.symbol])

        if self.this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
            primary_trait_tissue_values = primary_trait_tissue_vals_dict[self.this_trait.symbol.lower()]

            #print("trait_gene_symbols: ", pf(trait_gene_symbols.values()))
            corr_result_tissue_vals_dict= correlation_functions.get_trait_symbol_and_tissue_values(
                                                    symbol_list=self.trait_symbol_dict.values())

            #print("corr_result_tissue_vals: ", pf(corr_result_tissue_vals_dict))

            #print("trait_gene_symbols: ", pf(trait_gene_symbols))

            tissue_corr_data = {}
            for trait, symbol in self.trait_symbol_dict.iteritems():
                if symbol and symbol.lower() in corr_result_tissue_vals_dict:
                    this_trait_tissue_values = corr_result_tissue_vals_dict[symbol.lower()]

                    result = correlation_functions.cal_zero_order_corr_for_tiss(primary_trait_tissue_values,
                                                                          this_trait_tissue_values,
                                                                          self.corr_method)

                    tissue_corr_data[trait] = [symbol, result[0], result[2]]

            tissue_corr_data = collections.OrderedDict(sorted(tissue_corr_data.items(),
                                                           key=lambda t: -abs(t[1][1])))

            return tissue_corr_data

    def do_lit_correlation_for_trait_list(self):

        input_trait_mouse_gene_id = self.convert_to_mouse_gene_id(self.dataset.group.species.lower(), self.this_trait.geneid)

        for trait in self.correlation_results:

            if trait.geneid:
                trait.mouse_gene_id = self.convert_to_mouse_gene_id(self.dataset.group.species.lower(), trait.geneid)
            else:
                trait.mouse_gene_id = None

            if trait.mouse_gene_id and str(trait.mouse_gene_id).find(";") == -1:
                result = g.db.execute(
                    """SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId1='%s' and
                             GeneId2='%s'
                    """ % (escape(str(trait.mouse_gene_id)), escape(str(input_trait_mouse_gene_id)))
                ).fetchone()
                if not result:
                    result = g.db.execute("""SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId2='%s' and
                             GeneId1='%s'
                    """ % (escape(str(trait.mouse_gene_id)), escape(str(input_trait_mouse_gene_id)))
                    ).fetchone()

                if result:
                    lit_corr = result.value
                    trait.lit_corr = lit_corr
                else:
                    trait.lit_corr = 0
            else:
                trait.lit_corr = 0


    def do_lit_correlation_for_all_traits(self):
        input_trait_mouse_gene_id = self.convert_to_mouse_gene_id(self.dataset.group.species.lower(), self.this_trait.geneid)

        lit_corr_data = {}
        for trait, gene_id in self.trait_geneid_dict.iteritems():
            mouse_gene_id = self.convert_to_mouse_gene_id(self.dataset.group.species.lower(), gene_id)

            if mouse_gene_id and str(mouse_gene_id).find(";") == -1:
                #print("gene_symbols:", input_trait_mouse_gene_id + " / " + mouse_gene_id)
                result = g.db.execute(
                    """SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId1='%s' and
                             GeneId2='%s'
                    """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
                ).fetchone()
                if not result:
                    result = g.db.execute("""SELECT value
                       FROM LCorrRamin3
                       WHERE GeneId2='%s' and
                             GeneId1='%s'
                    """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
                    ).fetchone()
                if result:
                    #print("result:", result)
                    lit_corr = result.value
                    lit_corr_data[trait] = [gene_id, lit_corr]
                else:
                    lit_corr_data[trait] = [gene_id, 0]
            else:
                lit_corr_data[trait] = [gene_id, 0]

        lit_corr_data = collections.OrderedDict(sorted(lit_corr_data.items(),
                                                           key=lambda t: -abs(t[1][1])))

        return lit_corr_data

    def convert_to_mouse_gene_id(self, species=None, gene_id=None):
        """If the species is rat or human, translate the gene_id to the mouse geneid

        If there is no input gene_id or there's no corresponding mouse gene_id, return None

        """
        if not gene_id:
            return None

        mouse_gene_id = None

        if species == 'mouse':
            mouse_gene_id = gene_id

        elif species == 'rat':

            query = """SELECT mouse
                   FROM GeneIDXRef
                   WHERE rat='%s'""" % escape(gene_id)

            result = g.db.execute(query).fetchone()
            if result != None:
                mouse_gene_id = result.mouse

        elif species == 'human':

            query = """SELECT mouse
                   FROM GeneIDXRef
                   WHERE human='%s'""" % escape(gene_id)

            result = g.db.execute(query).fetchone()
            if result != None:
                mouse_gene_id = result.mouse

        return mouse_gene_id

    def get_sample_r_and_p_values(self, trait, target_samples):
        """Calculates the sample r (or rho) and p-value

        Given a primary trait and a target trait's sample values,
        calculates either the pearson r or spearman rho and the p-value
        using the corresponding scipy functions.

        """

        self.this_trait_vals = []
        target_vals = []
        for index, sample in enumerate(self.target_dataset.samplelist):
            if sample in self.sample_data:
                sample_value = self.sample_data[sample]
                target_sample_value = target_samples[index]
                self.this_trait_vals.append(sample_value)
                target_vals.append(target_sample_value)

        self.this_trait_vals, target_vals, num_overlap = corr_result_helpers.normalize_values(self.this_trait_vals, target_vals)

        #ZS: 2015 could add biweight correlation, see http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3465711/
        if self.corr_method == 'pearson':
            sample_r, sample_p = scipy.stats.pearsonr(self.this_trait_vals, target_vals)
        else:
            sample_r, sample_p = scipy.stats.spearmanr(self.this_trait_vals, target_vals)

        if num_overlap > 5:
            if numpy.isnan(sample_r):
                pass
            else:
                self.correlation_data[trait] = [sample_r, sample_p, num_overlap]

    def process_samples(self, start_vars, sample_names, excluded_samples=None):
        if not excluded_samples:
            excluded_samples = ()

        for sample in sample_names:
            if sample not in excluded_samples:
                # print("Looking for",sample,"in",start_vars)
                value = start_vars.get('value:' + sample)
                if value:
                    if not value.strip().lower() == 'x':
                        self.sample_data[str(sample)] = float(value)

def generate_corr_json(corr_results, this_trait, dataset, target_dataset, for_api = False):
    results_list = []
    for i, trait in enumerate(corr_results):
        results_dict = {}
        if not for_api:
            results_dict['checkbox'] = "<INPUT TYPE='checkbox' NAME='searchResult' class='checkbox trait_checkbox' style='padding-right: 0px;' VALUE='" + user_manager.data_hmac('{}:{}'.format(trait.name, trait.dataset.name)) + "'>"
            results_dict['index'] = i + 1
            results_dict['trait_id'] = "<a href='/show_trait?trait_id="+str(trait.name)+"&dataset="+str(dataset.name)+"'>"+str(trait.name)+"</a>"
        else:
            results_dict['trait_id'] = trait.name
        if target_dataset.type == "ProbeSet":
            results_dict['symbol'] = trait.symbol
            results_dict['description'] = trait.description_display
            results_dict['location'] = trait.location_repr
            results_dict['mean'] = float(trait.mean)
            if trait.LRS_score_repr != "N/A":
                results_dict['lrs_score'] = "%.1f" % float(trait.LRS_score_repr)
            else:
                results_dict['lrs_score'] = "N/A"
            results_dict['lrs_location'] = trait.LRS_location_repr
            if trait.additive != "":
                results_dict['additive'] = "%0.3f" % float(trait.additive)
            else:
                results_dict['additive'] = "N/A"
            if for_api:
                results_dict['sample_r'] = "%0.3f" % float(trait.sample_r)
            else:
                results_dict['sample_r'] = "<a target='_blank' href='corr_scatter_plot?dataset_1=" + str(dataset.name) + "&dataset_2=" + str(trait.dataset.name) + "&trait_1=" + str(this_trait.name) + "&trait_2=" + str(trait.name) + "'>" + "%0.3f" % float(trait.sample_r) + "</a>"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = "%0.3e" % float(trait.sample_p)
            if trait.lit_corr == "" or trait.lit_corr == 0:
                results_dict['lit_corr'] = "--"
            else:
                results_dict['lit_corr'] = "%0.3f" % float(trait.lit_corr)
            if trait.tissue_corr == "" or trait.tissue_corr == 0:
                results_dict['tissue_corr'] = "--"
            else:
                results_dict['tissue_corr'] = "%0.3f" % float(trait.tissue_corr)
        elif target_dataset.type == "Publish":
            results_dict['description'] = trait.description_display
            results_dict['authors'] = trait.authors
            if trait.pubmed_id:
                if for_api:
                    results_dict['pubmed_id'] = trait.pubmed_id
                    results_dict['year'] = trait.pubmed_text
                else:
                    results_dict['pubmed'] = "<a href='" + trait.pubmed_link + "'> " + trait.pubmed_text + "</a>"
            else:
                if for_api:
                    results_dict['pubmed_id'] = "N/A"
                    results_dict['year'] = "N/A"
                else:
                    results_dict['pubmed'] = "N/A"
            results_dict['lrs_score'] = trait.LRS_score_repr
            results_dict['lrs_location'] = trait.LRS_location_repr
            if trait.additive != "":
                results_dict['additive'] = "%0.3f" % float(trait.additive)
            else:
                results_dict['additive'] = "N/A"
            if for_api:
                results_dict['sample_r'] = "%0.3f" % trait.sample_r
            else:
                results_dict['sample_r'] = "<a target='_blank' href='corr_scatter_plot?dataset_1=" + str(dataset.name) + "&dataset_2=" + str(trait.dataset.name) + "&trait_1=" + str(this_trait.name) + "&trait_2=" + str(trait.name) + "'>" + "%0.3f" % trait.sample_r + "</a>"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = "%0.3e" % float(trait.sample_p)
        else:
            results_dict['lrs_location'] = trait.LRS_location_repr
            if for_api:
                results_dict['sample_r'] = "%0.3f" % trait.sample_r
            else:
                results_dict['sample_r'] = "<a target='_blank' href='corr_scatter_plot?dataset_1=" + str(dataset.name) + "&dataset_2=" + str(trait.dataset.name) + "&trait_1=" + str(this_trait.name) + "&trait_2=" + str(trait.name) + "'>" + "%0.3f" % float(trait.sample_r) + "</a>"
            results_dict['num_overlap'] = trait.num_overlap
            results_dict['sample_p'] = "%0.3e" % float(trait.sample_p)

        results_list.append(results_dict)

    return json.dumps(results_list)

def get_header_fields(data_type, corr_method):
    if data_type == "ProbeSet":
        if corr_method == "pearson":
            header_fields = ['Index',
                                'Record',
                                'Symbol',
                                'Description',
                                'Location',
                                'Mean',
                                'Sample r',
                                'N',
                                'Sample p(r)',
                                'Lit r',
                                'Tissue r',
                                'Tissue p(r)',
                                'Max LRS',
                                'Max LRS Location',
                                'Additive Effect']
        else:
            header_fields = ['Index',
                                'Record',
                                'Symbol',
                                'Description',
                                'Location',
                                'Mean',
                                'Sample rho',
                                'N',
                                'Sample p(rho)',
                                'Lit rho',
                                'Tissue rho',
                                'Tissue p(rho)',
                                'Max LRS',
                                'Max LRS Location',
                                'Additive Effect']
    elif data_type == "Publish":
        if corr_method == "pearson":
            header_fields = ['Index',
                            'Record',
                            'Description',
                            'Authors',
                            'Year',
                            'Sample r',
                            'N',
                            'Sample p(r)',
                            'Max LRS',
                            'Max LRS Location',
                            'Additive Effect']
        else:
            header_fields = ['Index',
                            'Record',
                            'Description',
                            'Authors',
                            'Year',
                            'Sample rho',
                            'N',
                            'Sample p(rho)',
                            'Max LRS',
                            'Max LRS Location',
                            'Additive Effect']
    else:
        if corr_method == "pearson":
            header_fields = ['Index',
                                'ID',
                                'Location',
                                'Sample r',
                                'N',
                                'Sample p(r)']
        else:
            header_fields = ['Index',
                                'ID',
                                'Location',
                                'Sample rho',
                                'N',
                                'Sample p(rho)']

    return header_fields