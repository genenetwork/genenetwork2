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

import datetime
import random
import string
import numpy as np
import scipy
from flask import current_app as app

from base.data_set import create_dataset

from utility.configuration import get_setting
from utility.helper_functions import get_trait_db_obs
from utility.corr_result_helpers import normalize_values
from utility.redis_tools import get_redis_conn


from gn3.computations.pca import compute_pca
from gn3.computations.pca import process_factor_loadings_tdata
from gn3.computations.pca import generate_pca_temp_traits
from gn3.computations.pca import cache_pca_dataset
from gn3.computations.pca import generate_scree_plot_data


class CorrelationMatrix:

    def __init__(self, start_vars):
        trait_db_list = [trait.strip()
                         for trait in start_vars['trait_list'].split(',')]

        get_trait_db_obs(self, trait_db_list)

        self.all_sample_list = []
        self.traits = []
        self.do_PCA = True
        # ZS: Getting initial group name before verifying all traits are in the same group in the following loop
        this_group = self.trait_list[0][1].group.name
        for trait_db in self.trait_list:
            this_group = trait_db[1].group.name
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

        # Shouldn't do PCA if there are more traits than observations/samples
        if len(this_trait_vals) < len(self.trait_list) or len(self.trait_list) < 3:
            self.do_PCA = False

        # ZS: Variable set to the lowest overlapping samples in order to notify user, or 8, whichever is lower (since 8 is when we want to display warning)
        self.lowest_overlap = 8

        self.corr_results = []
        self.pca_corr_results = []
        self.scree_data = []
        self.shared_samples_list = self.all_sample_list
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]

            this_db_samples = this_db.group.all_samples_ordered()
            this_sample_data = this_trait.data

            corr_result_row = []
            pca_corr_result_row = []
            is_spearman = False  # ZS: To determine if it's above or below the diagonal
            for target in self.trait_list:
                target_trait = target[0]
                target_db = target[1]
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
                    else:
                        if sample in self.shared_samples_list:
                            self.shared_samples_list.remove(sample)

                this_trait_vals, target_vals, num_overlap = normalize_values(
                    this_trait_vals, target_vals)

                if num_overlap < self.lowest_overlap:
                    self.lowest_overlap = num_overlap
                if num_overlap < 2:
                    corr_result_row.append([target_trait, 0, num_overlap])
                    pca_corr_result_row.append(0)
                else:
                    pearson_r, pearson_p = scipy.stats.pearsonr(
                        this_trait_vals, target_vals)
                    if is_spearman == False:
                        sample_r, sample_p = pearson_r, pearson_p
                        if sample_r > 0.999:
                            is_spearman = True
                    else:
                        sample_r, sample_p = scipy.stats.spearmanr(
                            this_trait_vals, target_vals)

                    corr_result_row.append(
                        [target_trait, sample_r, num_overlap])
                    pca_corr_result_row.append(pearson_r)

            self.corr_results.append(corr_result_row)
            self.pca_corr_results.append(pca_corr_result_row)

        self.export_filename, self.export_filepath = export_corr_matrix(
            self.corr_results)

        self.trait_data_array = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_db = trait_db[1]
            this_db_samples = this_db.group.all_samples_ordered()
            this_sample_data = this_trait.data

            this_trait_vals = []
            for index, sample in enumerate(this_db_samples):
                if (sample in this_sample_data) and (sample in self.shared_samples_list):
                    sample_value = this_sample_data[sample].value
                    this_trait_vals.append(sample_value)
            self.trait_data_array.append(this_trait_vals)

        groups = []
        for sample in self.all_sample_list:
            groups.append(1)

        self.pca_works = "False"
        try:

            if self.do_PCA:
                self.pca_works = "True"
                self.pca_trait_ids = []
                pca = self.calculate_pca()
                self.loadings_array = process_factor_loadings_tdata(
                    factor_loadings=self.loadings, traits_num=len(self.trait_list))

            else:
                self.pca_works = "False"
        except:
            self.pca_works = "False"

        self.js_data = dict(traits=[trait.name for trait in self.traits],
                            groups=groups,
                            scree_data = self.scree_data,
                            cols=list(range(len(self.traits))),
                            rows=list(range(len(self.traits))),
                            samples=self.all_sample_list,
                            sample_data=self.sample_data,)

    def calculate_pca(self):

        pca = compute_pca(self.pca_corr_results)

        self.loadings = pca["components"]
        self.scores = pca["scores"]
        self.pca_obj = pca["pca"]

        this_group_name = self.trait_list[0][1].group.name
        temp_dataset = create_dataset(
            dataset_name="Temp", dataset_type="Temp",
            group_name=this_group_name)
        temp_dataset.group.get_samplelist(redis_conn=get_redis_conn())

        pca_temp_traits = generate_pca_temp_traits(species=temp_dataset.group.species, group=this_group_name,
                                                   traits_data=self.trait_data_array, corr_array=self.pca_corr_results,
                                                   dataset_samples=temp_dataset.group.all_samples_ordered(),
                                                   shared_samples=self.shared_samples_list,
                                                   create_time=datetime.datetime.now().strftime("%m%d%H%M%S"))

        cache_pca_dataset(redis_conn=get_redis_conn(
        ), exp_days=60 * 60 * 24 * 30, pca_trait_dict=pca_temp_traits)

        self.pca_trait_ids = list(pca_temp_traits.keys())

        x_coord, y_coord = generate_scree_plot_data(
            list(self.pca_obj.explained_variance_ratio_))

        self.scree_data = {
            "x_coord": x_coord,
            "y_coord": y_coord
        }
        return pca


def export_corr_matrix(corr_results):
    corr_matrix_filename = "corr_matrix_" + \
        ''.join(random.choice(string.ascii_uppercase + string.digits)
                for _ in range(6))
    matrix_export_path = "{}{}.csv".format(
        get_setting(app, "WEBQTL_GENERATED_TEXT_DIR"), corr_matrix_filename)
    with open(matrix_export_path, "w+") as output_file:
        output_file.write(
            "Time/Date: " + datetime.datetime.now().strftime("%x / %X") + "\n")
        output_file.write("\n")
        output_file.write("Correlation ")
        for i, item in enumerate(corr_results[0]):
            output_file.write("Trait" + str(i + 1) + ": " +
                              str(item[0].dataset.name) + "::" + str(item[0].name) + "\t")
        output_file.write("\n")
        for i, row in enumerate(corr_results):
            output_file.write("Trait" + str(i + 1) + ": " +
                              str(row[0][0].dataset.name) + "::" + str(row[0][0].name) + "\t")
            for item in row:
                output_file.write(str(item[1]) + "\t")
            output_file.write("\n")

        output_file.write("\n")
        output_file.write("\n")
        output_file.write("N ")
        for i, item in enumerate(corr_results[0]):
            output_file.write("Trait" + str(i) + ": " +
                              str(item[0].dataset.name) + "::" + str(item[0].name) + "\t")
        output_file.write("\n")
        for i, row in enumerate(corr_results):
            output_file.write("Trait" + str(i) + ": " +
                              str(row[0][0].dataset.name) + "::" + str(row[0][0].name) + "\t")
            for item in row:
                output_file.write(str(item[2]) + "\t")
            output_file.write("\n")

    return corr_matrix_filename, matrix_export_path
