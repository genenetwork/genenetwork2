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
from gn2.wqflask.database import database_connection
from gn2.utility import helper_functions
from gn2.utility.tools import get_setting


class SendToGeneWeaver:
    def __init__(self, start_vars):
        trait_db_list = [trait.strip()
                         for trait in start_vars['trait_list'].split(',')]
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
                'client': "genenetwork",
                'species': species_name,
                'idtype': self.chip_name,
                'list': ",".join(trait_name_list),
            }


def get_trait_name_list(trait_list):
    name_list = []
    for trait_db in trait_list:
        name_list.append(trait_db[0].name)

    return name_list


def test_chip(trait_list):
    final_chip_name = ""
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        for trait_db in trait_list:
            dataset = trait_db[1]
            cursor.execute(
                "SELECT GeneChip.GO_tree_value "
                "FROM GeneChip, ProbeFreeze, ProbeSetFreeze "
                "WHERE GeneChip.Id = ProbeFreeze.ChipId "
                "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                "AND ProbeSetFreeze.Name = %s",
                (dataset.name,)
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
                        "SELECT GeneChip.Name "
                        "FROM GeneChip, ProbeFreeze, ProbeSetFreeze "
                        "WHERE GeneChip.Id = ProbeFreeze.ChipId "
                        "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                        "AND ProbeSetFreeze.Name = %s",
                        (dataset.name,)
                    )
                    chip_name = f'{cursor.fetchone()[0]}_NA'
                    return chip_name
            else:
                cursor.execute(
                    "SELECT GeneChip.Name FROM GeneChip, "
                    "ProbeFreeze, ProbeSetFreeze WHERE "
                    "GeneChip.Id = ProbeFreeze.ChipId "
                    "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                    "AND ProbeSetFreeze.Name = %s",
                    (dataset.name,)
                )
                if result := cursor.fetchone():
                    chip_name = f'{result[0]}_NA'
                    return chip_name
                return "not_microarray"

    return chip_name
