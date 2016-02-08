"""Script that generates the data for the main dropdown menus on the home page

Writes out data as /static/new/javascript/dataset_menu_structure.json
It needs to be run manually when database has been changed.

"""

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
# Contact Drs. Robert W. Williams
# at rwilliams@uthsc.edu 
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)

from __future__ import print_function, division

#from flask import config
#
#cdict = {}
#config = config.Config(cdict).from_envvar('WQFLASK_SETTINGS')
#print("cdict is:", cdict)

import sys
sys.path.append("/home/zas1024/")
import zach_settings

import MySQLdb

import simplejson as json
import urlparse


#import sqlalchemy as sa

from pprint import pformat as pf

#Engine = sa.create_engine(zach_settings.SQLALCHEMY_DATABASE_URI)

# build MySql database connection

#conn = Engine.connect()





def parse_db_uri(db_uri):
    """Converts a database URI to the db name, host name, user name, and password"""
    
    parsed_uri = urlparse.urlparse(zach_settings.DB_URI)
    
    db_conn_info = dict(
                        db = parsed_uri.path[1:],
                        host = parsed_uri.hostname,
                        user = parsed_uri.username,
                        passwd = parsed_uri.password)
    
    return db_conn_info



def get_species():
    """Build species list"""
    Cursor.execute("select Name, MenuName from Species order by OrderId")
    species = list(Cursor.fetchall())
    return species


def get_groups(species):
    """Build groups list"""
    groups = {}
    for species_name, _species_full_name in species:
        Cursor.execute("""select InbredSet.Name, InbredSet.FullName from InbredSet,
                       Species,
                       ProbeFreeze, GenoFreeze, PublishFreeze where Species.Name = %s
                       and InbredSet.SpeciesId = Species.Id and InbredSet.Name != 'BXD300' and
                       (PublishFreeze.InbredSetId = InbredSet.Id
                            or GenoFreeze.InbredSetId = InbredSet.Id
                            or ProbeFreeze.InbredSetId = InbredSet.Id)
                        group by InbredSet.Name
                        order by InbredSet.Name""", (species_name))
        groups[species_name] = list(Cursor.fetchall())
    return groups


def get_types(groups):
    """Build types list"""
    types = {}
    #print("Groups: ", pf(groups))
    for species, group_dict in groups.iteritems():
        types[species] = {}
        for group_name, _group_full_name in group_dict:
            # make group an alias to shorten the code
            #types[species][group_name] = [("Phenotypes", "Phenotypes"), ("Genotypes", "Genotypes")]
            if phenotypes_exist(group_name):
                types[species][group_name] = [("Phenotypes", "Phenotypes")]
            if genotypes_exist(group_name):
                if group_name in types[species]:
                    types[species][group_name] += [("Genotypes", "Genotypes")]
                else:
                    types[species][group_name] = [("Genotypes", "Genotypes")]
            if group_name in types[species]:
                types[species][group_name] += build_types(species, group_name)
            else:
                types[species][group_name] = build_types(species, group_name)

    return types


def phenotypes_exist(group_name):
    #print("group_name:", group_name)
    Cursor.execute("""select Name from PublishFreeze
                      where PublishFreeze.Name = %s""", (group_name+"Publish"))

    results = Cursor.fetchone()
    #print("RESULTS:", results)

    if results != None:
        return True
    else:
        return False

def genotypes_exist(group_name):
    #print("group_name:", group_name)
    Cursor.execute("""select Name from GenoFreeze
                      where GenoFreeze.Name = %s""", (group_name+"Geno"))

    results = Cursor.fetchone()
    #print("RESULTS:", results)

    if results != None:
        return True
    else:
        return False

def build_types(species, group):
    """Fetches tissues
    
    Gets the tissues with data for this species/group
    (all types except phenotype/genotype are tissues)
     
    """
    
    #print("""select distinct Tissue.Name
    #                   from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue, Species
    #                   where Species.Name = '{}' and Species.Id = InbredSet.SpeciesId and
    #                   InbredSet.Name = '{}' and
    #                   ProbeFreeze.TissueId = Tissue.Id and
    #                   ProbeFreeze.InbredSetId = InbredSet.Id and
    #                   ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
    #                   ProbeSetFreeze.public > 0
    #                   order by Tissue.Name""".format(species, group))
    Cursor.execute("""select distinct Tissue.Name
                       from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue, Species
                       where Species.Name = %s and Species.Id = InbredSet.SpeciesId and
                       InbredSet.Name = %s and
                       ProbeFreeze.TissueId = Tissue.Id and
                       ProbeFreeze.InbredSetId = InbredSet.Id and
                       ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
                       ProbeSetFreeze.public > 0
                       order by Tissue.Name""", (species, group))
    
    results = []
    for result in Cursor.fetchall():
        if len(result):
            results.append((result[0], result[0]))
    
    return results

def get_datasets(types):
    """Build datasets list"""
    datasets = {}
    for species, group_dict in types.iteritems():
        datasets[species] = {}
        for group, type_list in group_dict.iteritems():
            #print("type_list: ", type_list)
            datasets[species][group] = {}
            for type_name in type_list:
                datasets[species][group][type_name[0]] = build_datasets(species, group, type_name[0])
    return datasets


def build_datasets(species, group, type_name):
    """Gets dataset names from database"""
    dataset_text = dataset_value = None
    if type_name == "Phenotypes":
        dataset_value = "%sPublish" % group
        if group == 'MDP':
            dataset_text = "Mouse Phenome Database"
        else:
            dataset_text = "%s Published Phenotypes" % group

    elif type_name == "Genotypes":
        dataset_value = "%sGeno" % group
        dataset_text = "%s Genotypes" % group

    if dataset_value:
        return [(dataset_value, dataset_text)]
    else:
        #print("""select ProbeSetFreeze.Name, ProbeSetFreeze.FullName from
        #            ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue, Species where
        #            Species.Name = '{}' and Species.Id = InbredSet.SpeciesId and
        #            InbredSet.Name = '{}' and
        #            ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and Tissue.Name = '{}'
        #            and ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId =
        #            InbredSet.Id and ProbeSetFreeze.public > 0 order by
        #            ProbeSetFreeze.CreateTime desc""".format(species, group, type_name))
        Cursor.execute("""select ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName from
                    ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue, Species where
                    Species.Name = %s and Species.Id = InbredSet.SpeciesId and
                    InbredSet.Name = %s and
                    ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and Tissue.Name = %s
                    and ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId =
                    InbredSet.Id and ProbeSetFreeze.public > 0 order by
                    ProbeSetFreeze.CreateTime desc""", (species, group, type_name))
 
        dataset_results = Cursor.fetchall()
        datasets = []
        for dataset_info in dataset_results:
            this_dataset_info = []
            for info in dataset_info:
                this_dataset_info.append(str(info))
            datasets.append(this_dataset_info)

        return datasets


def main():
    """Generates and outputs (as json file) the data for the main dropdown menus on the home page"""

    parse_db_uri(zach_settings.DB_URI)

    species = get_species()
    groups = get_groups(species)
    print("groups:", groups)
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
                datasets=datasets,
                )

    #print("data:", data)

    output_file = """../wqflask/static/new/javascript/dataset_menu_structure.json"""

    with open(output_file, 'w') as fh:
        json.dump(data, fh, indent="   ", sort_keys=True)

    #print("\nWrote file to:", output_file)


def _test_it():
    """Used for internal testing only"""
    types = build_types("Mouse", "BXD")
    #print("build_types:", pf(types))
    datasets = build_datasets("Mouse", "BXD", "Hippocampus")
    #print("build_datasets:", pf(datasets))

if __name__ == '__main__':   
    Conn = MySQLdb.Connect(**parse_db_uri(zach_settings.DB_URI))
    Cursor = Conn.cursor()
    main()
