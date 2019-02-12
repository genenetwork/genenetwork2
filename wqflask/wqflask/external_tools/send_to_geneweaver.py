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

import string

from flask import Flask, g

from base.trait import GeneralTrait, retrieve_trait_info
from base.species import TheSpecies
from utility import helper_functions, corr_result_helpers

import utility.logger
logger = utility.logger.getLogger(__name__ )

class SendToGeneWeaver(object):
    def __init__(self, start_vars):
        trait_db_list = [trait.strip() for trait in start_vars['trait_list'].split(',')]
        helper_functions.get_trait_db_obs(self, trait_db_list)

        self.chip_name = test_chip(self.trait_list)
        self.wrong_input = "False"
        if self.chip_name == "mixed" or self.chip_name == "not_microarray" or '_NA' in self.chip_name:
            self.wrong_input = "True"
        else:
            species = self.trait_list[0][1].group.species
            if species == "rat":
                species_name = "Rattus norvegicus"
            elif species == "human":
                species_name = "Homo sapiens"
            elif species == "mouse":
                species_name = "Mus musculus"
            else:
                species_name = ""

            trait_name_list = get_trait_name_list(self.trait_list)

            self.hidden_vars = {
                                 'client'                     : "genenetwork",
                                 'species'                    : species_name,
                                 'idtype'                     : self.chip_name,
                                 'list'                       : string.join(trait_name_list, ","),
                               }

def get_trait_name_list(trait_list):
    name_list = []
    for trait_db in trait_list:
        name_list.append(trait_db[0].name)

    return name_list

def test_chip(trait_list):
    final_chip_name = ""

    for trait_db in trait_list:
        dataset = trait_db[1]
        result = g.db.execute("""SELECT GeneChip.GO_tree_value
                                 FROM GeneChip, ProbeFreeze, ProbeSetFreeze
                                 WHERE GeneChip.Id = ProbeFreeze.ChipId and
                                     ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
                                     ProbeSetFreeze.Name = '%s'"""  % dataset.name).fetchone()

        if result:
            chip_name = result[0]
            if chip_name:
                if chip_name != final_chip_name:
                    if final_chip_name:
                        return "mixed"
                    else:
                        final_chip_name = chip_name
                else:
                    pass
            else:
                result = g.db.execute("""SELECT GeneChip.Name
                                         FROM GeneChip, ProbeFreeze, ProbeSetFreeze
                                         WHERE GeneChip.Id = ProbeFreeze.ChipId and
                                               ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
                                               ProbeSetFreeze.Name = '%s'""" % dataset.name).fetchone()
                chip_name = '%s_NA' % result[0]
                return chip_name
        else:
            query = """SELECT GeneChip.Name
                                     FROM GeneChip, ProbeFreeze, ProbeSetFreeze
                                     WHERE GeneChip.Id = ProbeFreeze.ChipId and
                                           ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
                                           ProbeSetFreeze.Name = '%s'""" % dataset.name
            result = g.db.execute(query).fetchone()
            if result == None:
                return "not_microarray"
            else:
                chip_name = '%s_NA' % result[0]
                return chip_name

    return chip_name