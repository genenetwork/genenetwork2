from base import data_set
from base.trait import create_trait
from base.species import TheSpecies

from utility import hmac

from flask import g

import logging
logger = logging.getLogger(__name__)


def get_species_dataset_trait(self, start_vars):
    if "temp_trait" in list(start_vars.keys()):
        if start_vars['temp_trait'] == "True":
            self.dataset = data_set.create_dataset(
                dataset_name="Temp",
                dataset_type="Temp",
                group_name=start_vars['group'])
        else:
            self.dataset = data_set.create_dataset(start_vars['dataset'])
    else:
        self.dataset = data_set.create_dataset(start_vars['dataset'])
    logger.debug("After creating dataset")
    self.species = TheSpecies(dataset=self.dataset)
    logger.debug("After creating species")
    self.this_trait = create_trait(dataset=self.dataset,
                                   name=start_vars['trait_id'],
                                   cellid=None,
                                   get_qtl_info=True)
    logger.debug("After creating trait")


def get_trait_db_obs(self, trait_db_list):
    if isinstance(trait_db_list, str):
        trait_db_list = trait_db_list.split(",")

    self.trait_list = []
    for trait in trait_db_list:
        data, _separator, hmac_string = trait.rpartition(':')
        data = data.strip()
        assert hmac_string == hmac.hmac_creation(data), "Data tampering?"
        trait_name, dataset_name = data.split(":")
        if dataset_name == "Temp":
            dataset_ob = data_set.create_dataset(
                dataset_name=dataset_name, dataset_type="Temp",
                group_name=trait_name.split("_")[2])
        else:
            dataset_ob = data_set.create_dataset(dataset_name)
        trait_ob = create_trait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)
        if trait_ob:
            self.trait_list.append((trait_ob, dataset_ob))


def get_species_groups():
    """Group each species into a group"""
    _menu = {}
    for species, group_name in g.db.execute(
            "SELECT s.MenuName, i.InbredSetName FROM InbredSet i "
            "INNER JOIN Species s ON s.SpeciesId = i.SpeciesId "
            "ORDER BY i.SpeciesId ASC, i.Name ASC").fetchall():
        if _menu.get(species):
            _menu = _menu[species].append(group_name)
        else:
            _menu[species] = [group_name]
    return [{"species": key,
             "groups": value} for key, value in
            list(_menu.items())]
