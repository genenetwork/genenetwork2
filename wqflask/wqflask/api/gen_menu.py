from __future__ import print_function, division

import sys

from flask import g

from utility.tools import locate, locate_ignore_error, TEMPDIR, SQL_URI
from utility.benchmark import Bench

import MySQLdb

import urlparse

import utility.logger
logger = utility.logger.getLogger(__name__ )

def gen_dropdown_json():
    """Generates and outputs (as json file) the data for the main dropdown menus on the home page"""

    species = get_species()
    groups = get_groups(species)
    types = get_types(groups)
    datasets = get_datasets(types)

    species.append(('All Species', 'All Species'))
    groups['All Species'] = [('All Groups', 'All Groups')]
    types['All Species'] = {}
    types['All Species']['All Groups'] = [('Phenotypes', 'Phenotypes')]
    datasets['All Species'] = {}
    datasets['All Species']['All Groups'] = {}
    datasets['All Species']['All Groups']['Phenotypes'] = [('All Phenotypes','All Phenotypes')]

    data = dict(species=species,
                groups=groups,
                types=types,
                datasets=datasets)

    return data

def get_species():
    """Build species list"""
    results = g.db.execute("""SELECT Name, MenuName
                              FROM Species
                              WHERE Species.Name != 'macaque monkey'
                              ORDER BY OrderId""").fetchall()

    species = []
    for result in results:
        species.append([str(result[0]), str(result[1])])

    return species

def get_groups(species):
    """Build groups list"""
    groups = {}
    for species_name, _species_full_name in species:
        groups[species_name] = []
        # results = g.db.execute("""SELECT InbredSet.Name, InbredSet.FullName
        #                         FROM InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze
        #                         WHERE Species.Name = '{}' AND
        #                                 InbredSet.SpeciesId = Species.Id AND
        #                                 (PublishFreeze.InbredSetId = InbredSet.Id OR
        #                                 GenoFreeze.InbredSetId = InbredSet.Id OR
        #                                 ProbeFreeze.InbredSetId = InbredSet.Id)
        #                         GROUP by InbredSet.Name
        #                         ORDER BY InbredSet.FullName""".format(species_name)).fetchall()

        results = g.db.execute("""SELECT InbredSet.Name, InbredSet.FullName
                                FROM InbredSet, Species
                                WHERE Species.Name = '{}' AND
                                        InbredSet.SpeciesId = Species.Id
                                GROUP by InbredSet.Name
                                ORDER BY InbredSet.FullName""".format(species_name)).fetchall()

        for result in results:
            groups[species_name].append([str(result[0]), str(result[1])])

    return groups

def get_types(groups):
    """Build types list"""
    types = {}

    for species, group_dict in groups.iteritems():
        types[species] = {}
        for group_name, _group_full_name in group_dict:
            if phenotypes_exist(group_name):
                types[species][group_name] = [("Phenotypes", "Phenotypes")]
            if genotypes_exist(group_name):
                if group_name in types[species]:
                    types[species][group_name] += [("Genotypes", "Genotypes")]
                else:
                    types[species][group_name] = [("Genotypes", "Genotypes")]
            if group_name in types[species]:
                types_list = build_types(species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] += types_list
                else:
                    if not phenotypes_exist(group_name) and not genotypes_exist(group_name):
                        types[species].pop(group_name, None)
                        groups[species] = list(group for group in groups[species] if group[0] != group_name)
            else: #ZS: This whole else statement might be unnecessary, need to check
                types_list = build_types(species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] = types_list
                else:
                    types[species].pop(group_name, None)
                    groups[species] = list(group for group in groups[species] if group[0] != group_name)
    return types

def phenotypes_exist(group_name):
    results = g.db.execute("""SELECT Name
                              FROM PublishFreeze
                              WHERE PublishFreeze.Name = '{}'""".format(group_name+"Publish")).fetchone()

    if results != None:
        return True
    else:
        return False

def genotypes_exist(group_name):
    results = g.db.execute("""SELECT Name
                              FROM GenoFreeze
                              WHERE GenoFreeze.Name = '{}'""".format(group_name+"Geno")).fetchone()

    if results != None:
        return True
    else:
        return False

def build_types(species, group):
    """Fetches tissues

    Gets the tissues with data for this species/group
    (all types except phenotype/genotype are tissues)

    """

    query = """SELECT DISTINCT Tissue.Name
               FROM ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue, Species
               WHERE Species.Name = '{0}' AND
                     Species.Id = InbredSet.SpeciesId AND
                     InbredSet.Name = '{1}' AND
                     ProbeFreeze.TissueId = Tissue.Id AND
                     ProbeFreeze.InbredSetId = InbredSet.Id AND
                     ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND
                     ProbeSetFreeze.public > 0 AND
                     ProbeSetFreeze.confidentiality < 1
               ORDER BY Tissue.Name""".format(species, group)

    results = []
    for result in g.db.execute(query).fetchall():
        if len(result):
            these_datasets = build_datasets(species, group, result[0])
            if len(these_datasets) > 0:
                results.append([str(result[0]), str(result[0])])

    return results

def get_datasets(types):
    """Build datasets list"""
    datasets = {}
    for species, group_dict in types.iteritems():
        datasets[species] = {}
        for group, type_list in group_dict.iteritems():
            datasets[species][group] = {}
            for type_name in type_list:
                these_datasets = build_datasets(species, group, type_name[0])
                if len(these_datasets) > 0:
                    datasets[species][group][type_name[0]] = these_datasets

    return datasets


def build_datasets(species, group, type_name):
    """Gets dataset names from database"""
    dataset_text = dataset_value = None
    datasets = []
    if type_name == "Phenotypes":
        results = g.db.execute("""SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, PublishFreeze.FullName
                                  FROM InfoFiles, PublishFreeze, InbredSet
                                  WHERE InbredSet.Name = '{}' AND
                                        PublishFreeze.InbredSetId = InbredSet.Id AND
                                        InfoFiles.InfoPageName = PublishFreeze.Name
                                  ORDER BY PublishFreeze.CreateTime ASC""".format(group)).fetchall()

        if len(results) > 0:
            for result in results:
                dataset_id = str(result[0])
                dataset_value = str(result[1])
                if group == 'MDP':
                    dataset_text = "Mouse Phenome Database"
                else:
                    #dataset_text = "%s Phenotypes" % group
                    dataset_text = str(result[2])
                datasets.append([dataset_id, dataset_value, dataset_text])
        else:
            dataset_id = "None"
            dataset_value = "%sPublish" % group
            dataset_text = "%s Phenotypes" % group
            datasets.append([dataset_id, dataset_value, dataset_text])

    elif type_name == "Genotypes":
        results = g.db.execute("""SELECT InfoFiles.GN_AccesionId
                                  FROM InfoFiles, GenoFreeze, InbredSet
                                  WHERE InbredSet.Name = '{}' AND
                                        GenoFreeze.InbredSetId = InbredSet.Id AND
                                        InfoFiles.InfoPageName = GenoFreeze.ShortName AND
                                        GenoFreeze.public > 0 AND
                                        GenoFreeze.confidentiality < 1
                                  ORDER BY GenoFreeze.CreateTime DESC""".format(group)).fetchone()

        if results != None:
            dataset_id = str(results[0])
        else:
            dataset_id = "None"
        dataset_value = "%sGeno" % group
        dataset_text = "%s Genotypes" % group
        datasets.append([dataset_id, dataset_value, dataset_text])

    else: # for mRNA expression/ProbeSet
        results = g.db.execute("""SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName
                                  FROM ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue, Species
                                  WHERE Species.Name = '{0}' AND
                                        Species.Id = InbredSet.SpeciesId AND
                                        InbredSet.Name = '{1}' AND
                                        ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and Tissue.Name = '{2}' AND
                                        ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id AND
                                        ProbeSetFreeze.confidentiality < 1 and ProbeSetFreeze.public > 0
                                  ORDER BY ProbeSetFreeze.CreateTime DESC""".format(species, group, type_name)).fetchall()

        datasets = []
        for dataset_info in results:
            this_dataset_info = []
            for info in dataset_info:
                this_dataset_info.append(str(info))
            datasets.append(this_dataset_info)

    return datasets