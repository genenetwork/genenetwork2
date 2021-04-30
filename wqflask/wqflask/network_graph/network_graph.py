# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
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

import scipy
import simplejson as json

from base.trait import create_trait
from base import data_set
from utility import helper_functions
from utility import corr_result_helpers
from utility.tools import GN2_BRANCH_URL


class NetworkGraph:

    def __init__(self, start_vars):
        trait_db_list = [trait.strip()
                         for trait in start_vars['trait_list'].split(',')]

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

            this_trait_vals = []
            for sample in self.all_sample_list:
                if sample in this_sample_data:
                    this_trait_vals.append(this_sample_data[sample].value)
                else:
                    this_trait_vals.append('')
            self.sample_data.append(this_trait_vals)

        # ZS: Variable set to the lowest overlapping samples in order to notify user, or 8, whichever is lower (since 8 is when we want to display warning)
        self.lowest_overlap = 8

        self.nodes_list = []
        self.edges_list = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]

            this_db_samples = this_db.group.all_samples_ordered()
            this_sample_data = this_trait.data

            corr_result_row = []
            is_spearman = False  # ZS: To determine if it's above or below the diagonal

            max_corr = 0  # ZS: Used to determine whether node should be hidden when correlation coefficient slider is used

            for target in self.trait_list:
                target_trait = target[0]
                target_db = target[1]

                if str(this_trait) == str(target_trait) and str(this_db) == str(target_db):
                    continue

                target_samples = target_db.group.all_samples_ordered()

                target_sample_data = target_trait.data

                this_trait_vals = []
                target_vals = []
                for index, sample in enumerate(target_samples):

                    if (sample in this_sample_data) and (sample in target_sample_data):
                        sample_value = this_sample_data[sample].value
                        target_sample_value = target_sample_data[sample].value
                        this_trait_vals.append(sample_value)
                        target_vals.append(target_sample_value)

                this_trait_vals, target_vals, num_overlap = corr_result_helpers.normalize_values(
                    this_trait_vals, target_vals)

                if num_overlap < self.lowest_overlap:
                    self.lowest_overlap = num_overlap
                if num_overlap < 2:
                    continue
                else:
                    pearson_r, pearson_p = scipy.stats.pearsonr(
                        this_trait_vals, target_vals)
                    if is_spearman == False:
                        sample_r, sample_p = pearson_r, pearson_p
                        if sample_r == 1:
                            continue
                    else:
                        sample_r, sample_p = scipy.stats.spearmanr(
                            this_trait_vals, target_vals)

                    if -1 <= sample_r < -0.7:
                        color = "#0000ff"
                        width = 3
                    elif -0.7 <= sample_r < -0.5:
                        color = "#00ff00"
                        width = 2
                    elif -0.5 <= sample_r < 0:
                        color = "#000000"
                        width = 0.5
                    elif 0 <= sample_r < 0.5:
                        color = "#ffc0cb"
                        width = 0.5
                    elif 0.5 <= sample_r < 0.7:
                        color = "#ffa500"
                        width = 2
                    elif 0.7 <= sample_r <= 1:
                        color = "#ff0000"
                        width = 3
                    else:
                        color = "#000000"
                        width = 0

                    if abs(sample_r) > max_corr:
                        max_corr = abs(sample_r)

                    edge_data = {'id': str(this_trait.name) + '_to_' + str(target_trait.name),
                                 'source': str(this_trait.name) + ":" + str(this_trait.dataset.name),
                                 'target': str(target_trait.name) + ":" + str(target_trait.dataset.name),
                                 'correlation': round(sample_r, 3),
                                 'abs_corr': abs(round(sample_r, 3)),
                                 'p_value': round(sample_p, 3),
                                 'overlap': num_overlap,
                                 'color': color,
                                 'width': width}

                    edge_dict = {'data': edge_data}

                    self.edges_list.append(edge_dict)

            if trait_db[1].type == "ProbeSet":
                node_dict = {'data': {'id': str(this_trait.name) + ":" + str(this_trait.dataset.name),
                                      'label': this_trait.symbol,
                                      'symbol': this_trait.symbol,
                                      'geneid': this_trait.geneid,
                                      'omim': this_trait.omim,
                                      'max_corr': max_corr}}
            elif trait_db[1].type == "Publish":
                node_dict = {'data': {'id': str(this_trait.name) + ":" + str(this_trait.dataset.name),
                                      'label': this_trait.name,
                                      'max_corr': max_corr}}
            else:
                node_dict = {'data': {'id': str(this_trait.name) + ":" + str(this_trait.dataset.name),
                                      'label': this_trait.name,
                                      'max_corr': max_corr}}
            self.nodes_list.append(node_dict)

        self.elements = json.dumps(self.nodes_list + self.edges_list)
        self.gn2_url = GN2_BRANCH_URL

        groups = []
        for sample in self.all_sample_list:
            groups.append(1)

        self.js_data = dict(traits=[trait.name for trait in self.traits],
                            groups=groups,
                            cols=list(range(len(self.traits))),
                            rows=list(range(len(self.traits))),
                            samples=self.all_sample_list,
                            sample_data=self.sample_data,
                            elements=self.elements,)
