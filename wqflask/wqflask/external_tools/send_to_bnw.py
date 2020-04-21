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

from base.trait import GeneralTrait
from utility import helper_functions, corr_result_helpers

import utility.logger
logger = utility.logger.getLogger(__name__ )

class SendToBNW(object):
    def __init__(self, start_vars):
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        helper_functions.get_trait_db_obs(self, trait_db_list)

        trait_samples_list = []

        for trait_db in self.trait_list:
            trait_1 = trait_db[0]
            this_sample_data = trait_1.data

            trait1_samples = list(this_sample_data.keys())
            trait_samples_list.append(trait1_samples)

        shared_samples = list(set(trait_samples_list[0]).intersection(*trait_samples_list))

        self.form_value = "" #ZS: string that is passed to BNW through form
        values_list = []
        for trait_db in self.trait_list:
            this_trait = trait_db[0]
            this_sample_data = this_trait.data

            trait_vals = []
            for sample in this_sample_data:
                if sample in shared_samples:
                    trait_vals.append(this_sample_data[sample].value)

            values_list.append(trait_vals)
            self.form_value += "_" + str(this_trait.name) + ","

        values_list = zip(*values_list)
        self.form_value = self.form_value[:-1]
        self.form_value += ";"

        for row in values_list:
            has_none = False
            for cell in row:
                if not cell:
                    has_none = True
                    break
            if has_none:
                continue
            self.form_value += ",".join(str(cell) for cell in row)
            self.form_value += ";"