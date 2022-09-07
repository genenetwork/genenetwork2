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

import string

from wqflask.database import database_connection

from base.trait import GeneralTrait, retrieve_trait_info
from base.species import TheSpecies
from utility import helper_functions, corr_result_helpers


class SendToWebGestalt:
    def __init__(self, start_vars):
        trait_db_list = [trait.strip()
                         for trait in start_vars['trait_list'].split(',')]
        helper_functions.get_trait_db_obs(self, trait_db_list)

        self.chip_name = test_chip(self.trait_list)

        self.wrong_input = "False"
        if self.chip_name == "mixed" or self.chip_name == "not_microarray" or '_NA' in self.chip_name:
            self.wrong_input = "True"
        else:
            trait_name_list, gene_id_list = gen_gene_id_list(self.trait_list)

            self.target_url = "http://www.webgestalt.org/option.php"

            id_type = "entrezgene"

            self.hidden_vars = {
                'gene_list': "\n".join(gene_id_list),
                             'id_type': "entrezgene",
                             'ref_set': "genome",
                             'enriched_database_category': "geneontology",
                             'enriched_database_name': "Biological_Process",
                             'sig_method': "fdr",
                             'sig_value': "0.05",
                             'enrich_method': "ORA",
                             'fdr_method': "BH",
                             'min_num': "2"
            }

            species = self.trait_list[0][1].group.species
            if species == "rat":
                self.hidden_vars['organism'] = "rnorvegicus"
            elif species == "human":
                self.hidden_vars['organism'] = "hsapiens"
            elif species == "mouse":
                self.hidden_vars['organism'] = "mmusculus"
            else:
                self.hidden_vars['organism'] = "others"


def test_chip(trait_list):
    final_chip_name = ""
    with database_connection() as conn, conn.cursor() as cursor:
        for trait_db in trait_list:
            dataset = trait_db[1]
            cursor.execute(
                "SELECT GeneChip.GO_tree_value "
                "FROM GeneChip, ProbeFreeze, "
                "ProbeSetFreeze WHERE "
                "GeneChip.Id = ProbeFreeze.ChipId "
                "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                "AND ProbeSetFreeze.Name = %s", (dataset.name,)
            )

            if result := cursor.fetchone():
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
                    cursor.execute(
                        "SELECT GeneChip.Name FROM GeneChip, ProbeFreeze, "
                        "ProbeSetFreeze WHERE "
                        "GeneChip.Id = ProbeFreeze.ChipId AND "
                        "ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                        "AND ProbeSetFreeze.Name = %s", (dataset.name,)
                    )
                    result = cursor.fetchone()
                    chip_name = f'{result[0]}_NA'
                    return chip_name
            else:
                cursor.execute(
                    "SELECT GeneChip.Name FROM GeneChip, ProbeFreeze, "
                    "ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId "
                    "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND "
                    "ProbeSetFreeze.Name = %s", (dataset.name,)
                )
                result = cursor.fetchone()
                if not result:
                    return "not_microarray"
                else:
                    chip_name = f'{result[0]}_NA'
                    return chip_name
    return chip_name


def gen_gene_id_list(trait_list):
    trait_name_list = []
    gene_id_list = []
    for trait_db in trait_list:
        trait = trait_db[0]
        trait_name_list.append(trait.name)
        retrieve_trait_info(trait, trait.dataset)
        gene_id_list.append(str(trait.geneid))
    return trait_name_list, gene_id_list
