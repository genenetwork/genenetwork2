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
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
# This module is used by GeneNetwork project (www.genenetwork.org)

from __future__ import absolute_import, print_function, division
import os
import math
import string
import collections
import codecs

import json
import requests
import gzip
import cPickle as pickle
import itertools

from redis import Redis
Redis = Redis()

from flask import Flask, g

import reaper

from base import webqtlConfig
from base import species
from db import webqtlDatabaseFunction
from utility import webqtlUtil
from utility.benchmark import Bench
from utility import chunks
from utility import gen_geno_ob
from utility.tools import locate, locate_ignore_error, flat_files

from wqflask.api import gen_menu

from maintenance import get_group_samplelists

from MySQLdb import escape_string as escape
from pprint import pformat as pf
from db.gn_server import menu_main
from db.call import fetchall,fetchone,fetch1

from utility.tools import USE_GN_SERVER, USE_REDIS, flat_files, flat_file_exists
from utility.logger import getLogger
logger = getLogger(__name__ )

# Used by create_database to instantiate objects
# Each subclass will add to this
DS_NAME_MAP = {}

def create_dataset(dataset_name, rebuild=True, dataset_type = None, get_samplelist = True, group_name = None):
    if not dataset_type:
        dataset_type = Dataset_Getter(dataset_name)
        logger.debug("dataset_type", dataset_type)

    dataset_ob = DS_NAME_MAP[dataset_type]
    dataset_class = globals()[dataset_ob]
    if dataset_type == "Temp":
        return dataset_class(dataset_name, get_samplelist, group_name)
    else:
        return dataset_class(dataset_name, get_samplelist)

class Dataset_Types(object):

    def __init__(self, rebuild=False):
        """Create a dictionary of samples where the value is set to Geno,
Publish or ProbeSet. E.g.

        {'AD-cases-controls-MyersGeno': 'Geno',
         'AD-cases-controls-MyersPublish': 'Publish',
         'AKXDGeno': 'Geno',
         'AXBXAGeno': 'Geno',
         'AXBXAPublish': 'Publish',
         'Aging-Brain-UCIPublish': 'Publish',
         'All Phenotypes': 'Publish',
         'B139_K_1206_M': 'ProbeSet',
         'B139_K_1206_R': 'ProbeSet' ...

        """
        self.datasets = {}
        if rebuild: #ZS: May make this the only option
            data = json.loads(requests.get("http://gn2.genenetwork.org/api/v_pre1/gen_dropdown").content)
            logger.debug("THE DATA:", data)
            #data = gen_menu.gen_dropdown_json()
        else:
            file_name = "wqflask/static/new/javascript/dataset_menu_structure.json"
            with open(file_name, 'r') as fh:
                data = json.load(fh)

        for species in data['datasets']:
            for group in data['datasets'][species]:
                for dataset_type in data['datasets'][species][group]:
                    for dataset in data['datasets'][species][group][dataset_type]:
                        short_dataset_name = dataset[1]
                        if dataset_type == "Phenotypes":
                            new_type = "Publish"
                        elif dataset_type == "Genotypes":
                            new_type = "Geno"
                        else:
                            new_type = "ProbeSet"
                        self.datasets[short_dataset_name] = new_type

        # Set LOG_LEVEL_DEBUG=5 to see the following:
        logger.debugf(5, "datasets",self.datasets)

    def __call__(self, name):
        return self.datasets[name]

# Do the intensive work at startup one time only
Dataset_Getter = Dataset_Types()

def create_datasets_list():
    if USE_REDIS:
        key = "all_datasets"
        result = Redis.get(key)

        if result:
            logger.debug("Redis cache hit")
            datasets = pickle.loads(result)

    if result is None:
        datasets = list()
        with Bench("Creating DataSets object"):
            type_dict = {'Publish': 'PublishFreeze',
                         'ProbeSet': 'ProbeSetFreeze',
                         'Geno': 'GenoFreeze'}

            for dataset_type in type_dict:
                query = "SELECT Name FROM {}".format(type_dict[dataset_type])
                for result in fetchall(query):
                    #The query at the beginning of this function isn't
                    #necessary here, but still would rather just reuse
                    #it logger.debug("type: {}\tname:
                    #{}".format(dataset_type, result.Name))
                    dataset = create_dataset(result.Name, dataset_type)
                    datasets.append(dataset)

        if USE_REDIS:
            Redis.set(key, pickle.dumps(datasets, pickle.HIGHEST_PROTOCOL))
            Redis.expire(key, 60*60)

    return datasets


def create_in_clause(items):
    """Create an in clause for mysql"""
    in_clause = ', '.join("'{}'".format(x) for x in mescape(*items))
    in_clause = '( {} )'.format(in_clause)
    return in_clause


def mescape(*items):
    """Multiple escape"""
    escaped = [escape(str(item)) for item in items]
    #logger.debug("escaped is:", escaped)
    return escaped


class Markers(object):
    """Todo: Build in cacheing so it saves us reading the same file more than once"""
    def __init__(self, name):
        json_data_fh = open(locate(name + ".json",'genotype/json'))

        markers = []
        with open("%s/%s_snps.txt" % (flat_files('genotype/bimbam'), name), 'r') as bimbam_fh:
            if len(bimbam_fh.readline().split(", ")) > 2:
                delimiter = ", "
            elif len(bimbam_fh.readline().split(",")) > 2:
                delimiter = ","
            elif len(bimbam_fh.readline().split("\t")) > 2:
                delimiter = "\t"
            else:
                delimiter = " "
            for line in bimbam_fh:
                marker = {}
                marker['name'] = line.split(delimiter)[0].rstrip()
                marker['Mb'] = float(line.split(delimiter)[1].rstrip())/1000000
                marker['chr'] = line.split(delimiter)[2].rstrip()
                markers.append(marker)

        for marker in markers:
            if (marker['chr'] != "X") and (marker['chr'] != "Y"):
                marker['chr'] = int(marker['chr'])
            marker['Mb'] = float(marker['Mb'])

        self.markers = markers

    def add_pvalues(self, p_values):
        logger.debug("length of self.markers:", len(self.markers))
        logger.debug("length of p_values:", len(p_values))

        if type(p_values) is list:
            # THIS IS only needed for the case when we are limiting the number of p-values calculated
            #if len(self.markers) > len(p_values):
            #    self.markers = self.markers[:len(p_values)]

            for marker, p_value in itertools.izip(self.markers, p_values):
                if not p_value:
                    continue
                marker['p_value'] = float(p_value)
                if math.isnan(marker['p_value']) or marker['p_value'] <= 0:
                    marker['lod_score'] = 0
                    marker['lrs_value'] = 0
                else:
                    marker['lod_score'] = -math.log10(marker['p_value'])
                    #Using -log(p) for the LRS; need to ask Rob how he wants to get LRS from p-values
                    marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
        elif type(p_values) is dict:
            filtered_markers = []
            for marker in self.markers:
                #logger.debug("marker[name]", marker['name'])
                #logger.debug("p_values:", p_values)
                if marker['name'] in p_values:
                    #logger.debug("marker {} IS in p_values".format(i))
                    marker['p_value'] = p_values[marker['name']]
                    if math.isnan(marker['p_value']) or (marker['p_value'] <= 0):
                        marker['lod_score'] = 0
                        marker['lrs_value'] = 0
                    else:
                        marker['lod_score'] = -math.log10(marker['p_value'])
                        #Using -log(p) for the LRS; need to ask Rob how he wants to get LRS from p-values
                        marker['lrs_value'] = -math.log10(marker['p_value']) * 4.61
                    filtered_markers.append(marker)
                #else:
                    #logger.debug("marker {} NOT in p_values".format(i))
                    #self.markers.remove(marker)
                    #del self.markers[i]
            self.markers = filtered_markers

class HumanMarkers(Markers):

    def __init__(self, name, specified_markers = []):
        marker_data_fh = open(flat_files('mapping') + '/' + name + '.bim')
        self.markers = []
        for line in marker_data_fh:
            splat = line.strip().split()
            #logger.debug("splat:", splat)
            if len(specified_markers) > 0:
                if splat[1] in specified_markers:
                    marker = {}
                    marker['chr'] = int(splat[0])
                    marker['name'] = splat[1]
                    marker['Mb'] = float(splat[3]) / 1000000
                else:
                    continue
            else:
                marker = {}
                marker['chr'] = int(splat[0])
                marker['name'] = splat[1]
                marker['Mb'] = float(splat[3]) / 1000000
            self.markers.append(marker)

        #logger.debug("markers is: ", pf(self.markers))


    def add_pvalues(self, p_values):
        super(HumanMarkers, self).add_pvalues(p_values)


class DatasetGroup(object):
    """
    Each group has multiple datasets; each species has multiple groups.

    For example, Mouse has multiple groups (BXD, BXA, etc), and each group
    has multiple datasets associated with it.

    """
    def __init__(self, dataset, name=None):
        """This sets self.group and self.group_id"""
        if name == None:
            self.name, self.id, self.genetic_type = fetchone(dataset.query_for_group)
        else:
            self.name, self.id, self.genetic_type = fetchone("SELECT InbredSet.Name, InbredSet.Id, InbredSet.GeneticType FROM InbredSet where Name='%s'" % name)
        if self.name == 'BXD300':
            self.name = "BXD"

        self.f1list = None
        self.parlist = None
        self.get_f1_parent_strains()

        self.mapping_id, self.mapping_names = self.get_mapping_methods()

        self.species = webqtlDatabaseFunction.retrieve_species(self.name)

        self.incparentsf1 = False
        self.allsamples = None
        self._datasets = None
        self.genofile = None

    def get_mapping_methods(self):

        mapping_id = g.db.execute("select MappingMethodId from InbredSet where Name= '%s'" % self.name).fetchone()[0]
        if mapping_id == "1":
            mapping_names = ["QTLReaper", "R/qtl"]
        elif mapping_id == "2":
            mapping_names = ["GEMMA"]
        elif mapping_id == "4":
            mapping_names = ["GEMMA", "PLINK"]
        else:
            mapping_names = []

        return mapping_id, mapping_names

    def get_markers(self):
        def check_plink_gemma():
            if flat_file_exists("mapping"):
                MAPPING_PATH = flat_files("mapping")+"/"
                if os.path.isfile(MAPPING_PATH+self.name+".bed"):
                    return True
            return False

        if check_plink_gemma():
            marker_class = HumanMarkers
        else:
            marker_class = Markers

        if self.genofile:
            self.markers = marker_class(self.genofile[:-5])
        else:
            self.markers = marker_class(self.name)

    def get_f1_parent_strains(self):
        try:
            # NL, 07/27/2010. ParInfo has been moved from webqtlForm.py to webqtlUtil.py;
            f1, f12, maternal, paternal = webqtlUtil.ParInfo[self.name]
        except KeyError:
            f1 = f12 = maternal = paternal = None

        if f1 and f12:
            self.f1list = [f1, f12]
        if maternal and paternal:
            self.parlist = [maternal, paternal]

    def get_samplelist(self):
        result = None
        key = "samplelist:v3:" + self.name
        if USE_REDIS:
            result = Redis.get(key)

        if result is not None:
            self.samplelist = json.loads(result)
        else:
            logger.debug("Cache not hit")

            genotype_fn = locate_ignore_error(self.name+".geno",'genotype')
            if genotype_fn:
                self.samplelist = get_group_samplelists.get_samplelist("geno", genotype_fn)
            else:
                self.samplelist = None

            if USE_REDIS:
                Redis.set(key, json.dumps(self.samplelist))
                Redis.expire(key, 60*5)

    def all_samples_ordered(self):
        result = []
        lists = (self.parlist, self.f1list, self.samplelist)
        [result.extend(l) for l in lists if l]
        return result

    def read_genotype_file(self, use_reaper=False):
        '''Read genotype from .geno file instead of database'''
        #genotype_1 is Dataset Object without parents and f1
        #genotype_2 is Dataset Object with parents and f1 (not for intercross)

        #genotype_1 = reaper.Dataset()

        # reaper barfs on unicode filenames, so here we ensure it's a string
        if self.genofile:
            full_filename = str(locate(self.genofile, 'genotype'))
        else:
            full_filename = str(locate(self.name + '.geno', 'genotype'))

        if use_reaper:
            genotype_1 = reaper.Dataset()
            genotype_1.read(full_filename)
        else:
            genotype_1 = gen_geno_ob.genotype(full_filename)

        if genotype_1.type == "group" and self.parlist:
            genotype_2 = genotype_1.add(Mat=self.parlist[0], Pat=self.parlist[1])       #, F1=_f1)
        else:
            genotype_2 = genotype_1

        #determine default genotype object
        if self.incparentsf1 and genotype_1.type != "intercross":
            genotype = genotype_2
        else:
            self.incparentsf1 = 0
            genotype = genotype_1

        self.samplelist = list(genotype.prgy)

        return genotype

def datasets(group_name, this_group = None):
    key = "group_dataset_menu:v2:" + group_name
    logger.debug("key is2:", key)
    dataset_menu = []
    logger.debug("[tape4] webqtlConfig.PUBLICTHRESH:", webqtlConfig.PUBLICTHRESH)
    logger.debug("[tape4] type webqtlConfig.PUBLICTHRESH:", type(webqtlConfig.PUBLICTHRESH))
    the_results = fetchall('''
         (SELECT '#PublishFreeze',PublishFreeze.FullName,PublishFreeze.Name
          FROM PublishFreeze,InbredSet
          WHERE PublishFreeze.InbredSetId = InbredSet.Id
            and InbredSet.Name = '%s'
            and PublishFreeze.public > %s
            and PublishFreeze.confidentiality < 1
          ORDER BY PublishFreeze.Id ASC)
         UNION
         (SELECT '#GenoFreeze',GenoFreeze.FullName,GenoFreeze.Name
          FROM GenoFreeze, InbredSet
          WHERE GenoFreeze.InbredSetId = InbredSet.Id
            and InbredSet.Name = '%s'
            and GenoFreeze.public > %s
            and GenoFreeze.confidentiality < 1)
         UNION
         (SELECT Tissue.Name, ProbeSetFreeze.FullName,ProbeSetFreeze.Name
          FROM ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue
          WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
            and ProbeFreeze.TissueId = Tissue.Id
            and ProbeFreeze.InbredSetId = InbredSet.Id
            and InbredSet.Name like %s
            and ProbeSetFreeze.public > %s
            and ProbeSetFreeze.confidentiality < 1
          ORDER BY Tissue.Name, ProbeSetFreeze.OrderList DESC)
        ''' % (group_name, webqtlConfig.PUBLICTHRESH,
              group_name, webqtlConfig.PUBLICTHRESH,
              "'" + group_name + "'", webqtlConfig.PUBLICTHRESH))

    sorted_results = sorted(the_results, key=lambda kv: kv[0])

    pheno_inserted = False #ZS: This is kind of awkward, but need to ensure Phenotypes show up before Genotypes in dropdown
    geno_inserted = False
    for dataset_item in sorted_results:
        tissue_name = dataset_item[0]
        dataset = dataset_item[1]
        dataset_short = dataset_item[2]
        if tissue_name in ['#PublishFreeze', '#GenoFreeze']:
            if tissue_name == '#PublishFreeze' and (dataset_short == group_name + 'Publish'):
                dataset_menu.insert(0, dict(tissue=None, datasets=[(dataset, dataset_short)]))
                pheno_inserted = True
            elif pheno_inserted and tissue_name == '#GenoFreeze':
                dataset_menu.insert(1, dict(tissue=None, datasets=[(dataset, dataset_short)]))
                geno_inserted = True
            else:
                dataset_menu.append(dict(tissue=None, datasets=[(dataset, dataset_short)]))
        else:
            tissue_already_exists = False
            for i, tissue_dict in enumerate(dataset_menu):
                if tissue_dict['tissue'] == tissue_name:
                    tissue_already_exists = True
                    break

            if tissue_already_exists:
                #logger.debug("dataset_menu:", dataset_menu[i]['datasets'])
                dataset_menu[i]['datasets'].append((dataset, dataset_short))
            else:
                dataset_menu.append(dict(tissue=tissue_name,
                                    datasets=[(dataset, dataset_short)]))

    if USE_REDIS:
        Redis.set(key, pickle.dumps(dataset_menu, pickle.HIGHEST_PROTOCOL))
        Redis.expire(key, 60*5)

    if this_group != None:
        this_group._datasets = dataset_menu
        return this_group._datasets
    else:
        return dataset_menu

class DataSet(object):
    """
    DataSet class defines a dataset in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input dataset(temp)

    """

    def __init__(self, name, get_samplelist = True, group_name = None):

        assert name, "Need a name"
        self.name = name
        self.id = None
        self.shortname = None
        self.fullname = None
        self.type = None
        self.data_scale = None #ZS: For example log2

        self.setup()

        if self.type == "Temp": #Need to supply group name as input if temp trait
            self.group = DatasetGroup(self, name=group_name)   # sets self.group and self.group_id and gets genotype
        else:
            self.check_confidentiality()
            self.retrieve_other_names()
            self.group = DatasetGroup(self)   # sets self.group and self.group_id and gets genotype
            self.accession_id = self.get_accession_id()
        if get_samplelist == True:
             self.group.get_samplelist()
        self.species = species.TheSpecies(self)


    def get_desc(self):
        """Gets overridden later, at least for Temp...used by trait's get_given_name"""
        return None

    # Delete this eventually
    @property
    def riset():
        Weve_Renamed_This_As_Group

    def get_accession_id(self):
        if self.type == "Publish":
            results = g.db.execute("""select InfoFiles.GN_AccesionId from InfoFiles, PublishFreeze, InbredSet where
                        InbredSet.Name = %s and
                        PublishFreeze.InbredSetId = InbredSet.Id and
                        InfoFiles.InfoPageName = PublishFreeze.Name and
                        PublishFreeze.public > 0 and
                        PublishFreeze.confidentiality < 1 order by
                        PublishFreeze.CreateTime desc""", (self.group.name)).fetchone()
        elif self.type == "Geno":
            results = g.db.execute("""select InfoFiles.GN_AccesionId from InfoFiles, GenoFreeze, InbredSet where
                        InbredSet.Name = %s and
                        GenoFreeze.InbredSetId = InbredSet.Id and
                        InfoFiles.InfoPageName = GenoFreeze.ShortName and
                        GenoFreeze.public > 0 and
                        GenoFreeze.confidentiality < 1 order by
                        GenoFreeze.CreateTime desc""", (self.group.name)).fetchone()
        else:
            results = None

        if results != None:
            return str(results[0])
        else:
            return "None"

    def retrieve_other_names(self):
        """This method fetches the the dataset names in search_result.

        If the data set name parameter is not found in the 'Name' field of
        the data set table, check if it is actually the FullName or
        ShortName instead.

        This is not meant to retrieve the data set info if no name at
        all is passed.

        """


        try:
            if self.type == "ProbeSet":
                query_args = tuple(escape(x) for x in (
                    str(webqtlConfig.PUBLICTHRESH),
                    self.name,
                    self.name,
                    self.name))

                self.id, self.name, self.fullname, self.shortname, self.data_scale, self.tissue = fetch1("""
SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.FullName, ProbeSetFreeze.ShortName, ProbeSetFreeze.DataScale, Tissue.Name
FROM ProbeSetFreeze, ProbeFreeze, Tissue
WHERE ProbeSetFreeze.public > %s
AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
AND ProbeFreeze.TissueId = Tissue.Id
AND (ProbeSetFreeze.Name = '%s' OR ProbeSetFreeze.FullName = '%s' OR ProbeSetFreeze.ShortName = '%s')
                """ % (query_args),"/dataset/"+self.name+".json",
            lambda r: (r["id"],r["name"],r["full_name"],r["short_name"],r["data_scale"],r["tissue"])
                )
            else:
                query_args = tuple(escape(x) for x in (
                    (self.type + "Freeze"),
                    str(webqtlConfig.PUBLICTHRESH),
                    self.name,
                    self.name,
                    self.name))

                self.tissue = "N/A"
                self.id, self.name, self.fullname, self.shortname = fetchone("""
                        SELECT Id, Name, FullName, ShortName
                        FROM %s
                        WHERE public > %s AND
                             (Name = '%s' OR FullName = '%s' OR ShortName = '%s')
                  """ % (query_args))

        except TypeError:
            logger.debug("Dataset {} is not yet available in GeneNetwork.".format(self.name))
            pass

    def get_trait_data(self, sample_list=None):
        if sample_list:
            self.samplelist = sample_list
        else:
            self.samplelist = self.group.samplelist

        if self.group.parlist != None and self.group.f1list != None:
            if (self.group.parlist + self.group.f1list) in self.samplelist:
                self.samplelist += self.group.parlist + self.group.f1list

        query = """
            SELECT Strain.Name, Strain.Id FROM Strain, Species
            WHERE Strain.Name IN {}
            and Strain.SpeciesId=Species.Id
            and Species.name = '{}'
            """.format(create_in_clause(self.samplelist), *mescape(self.group.species))
        logger.sql(query)
        results = dict(g.db.execute(query).fetchall())
        sample_ids = [results[item] for item in self.samplelist]

        # MySQL limits the number of tables that can be used in a join to 61,
        # so we break the sample ids into smaller chunks
        # Postgres doesn't have that limit, so we can get rid of this after we transition
        chunk_size = 50
        number_chunks = int(math.ceil(len(sample_ids) / chunk_size))
        trait_sample_data = []
        for sample_ids_step in chunks.divide_into_chunks(sample_ids, number_chunks):
            if self.type == "Publish":
                dataset_type = "Phenotype"
            else:
                dataset_type = self.type
            temp = ['T%s.value' % item for item in sample_ids_step]
            if self.type == "Publish":
                query = "SELECT {}XRef.Id,".format(escape(self.type))
            else:
                query = "SELECT {}.Name,".format(escape(dataset_type))
            data_start_pos = 1
            query += string.join(temp, ', ')
            query += ' FROM ({}, {}XRef, {}Freeze) '.format(*mescape(dataset_type,
                                                                     self.type,
                                                                     self.type))

            for item in sample_ids_step:
                query += """
                        left join {}Data as T{} on T{}.Id = {}XRef.DataId
                        and T{}.StrainId={}\n
                        """.format(*mescape(self.type, item, item, self.type, item, item))

            if self.type == "Publish":
                query += """
                        WHERE {}XRef.InbredSetId = {}Freeze.InbredSetId
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(self.type, self.type, self.type, self.name,
                                    dataset_type, self.type, dataset_type, dataset_type))
            else:
                query += """
                        WHERE {}XRef.{}FreezeId = {}Freeze.Id
                        and {}Freeze.Name = '{}'
                        and {}.Id = {}XRef.{}Id
                        order by {}.Id
                        """.format(*mescape(self.type, self.type, self.type, self.type,
                                   self.name, dataset_type, self.type, self.type, dataset_type))

            #logger.debug("trait data query: ", query)

            logger.sql(query)
            results = g.db.execute(query).fetchall()
            #logger.debug("query results:", results)
            trait_sample_data.append(results)

        trait_count = len(trait_sample_data[0])
        self.trait_data = collections.defaultdict(list)

        # put all of the separate data together into a dictionary where the keys are
        # trait names and values are lists of sample values
        for trait_counter in range(trait_count):
            trait_name = trait_sample_data[0][trait_counter][0]
            for chunk_counter in range(int(number_chunks)):
                self.trait_data[trait_name] += (
                    trait_sample_data[chunk_counter][trait_counter][data_start_pos:])

class PhenotypeDataSet(DataSet):
    DS_NAME_MAP['Publish'] = 'PhenotypeDataSet'

    def setup(self):

        #logger.debug("IS A PHENOTYPEDATASET")

        # Fields in the database table
        self.search_fields = ['Phenotype.Post_publication_description',
                            'Phenotype.Pre_publication_description',
                            'Phenotype.Pre_publication_abbreviation',
                            'Phenotype.Post_publication_abbreviation',
                            'Phenotype.Lab_code',
                            'Publication.PubMed_ID',
                            'Publication.Abstract',
                            'Publication.Title',
                            'Publication.Authors',
                            'PublishXRef.Id']

        # Figure out what display_fields is
        self.display_fields = ['name', 'group_code',
                               'pubmed_id',
                               'pre_publication_description',
                               'post_publication_description',
                               'original_description',
                               'pre_publication_abbreviation',
                               'post_publication_abbreviation',
                               'lab_code',
                               'submitter', 'owner',
                               'authorized_users',
                               'authors', 'title',
                               'abstract', 'journal',
                               'volume', 'pages',
                               'month', 'year',
                               'sequence', 'units', 'comments']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                            'Record',
                            'Description',
                            'Authors',
                            'Year',
                            'Max LRS',
                            'Max LRS Location',
                            'Additive Effect']

        self.type = 'Publish'

        self.query_for_group = '''
                            SELECT
                                    InbredSet.Name, InbredSet.Id, InbredSet.GeneticType
                            FROM
                                    InbredSet, PublishFreeze
                            WHERE
                                    PublishFreeze.InbredSetId = InbredSet.Id AND
                                    PublishFreeze.Name = "%s"
                    ''' % escape(self.name)

    def check_confidentiality(self):
        # (Urgently?) Need to write this
        pass

    def get_trait_info(self, trait_list, species = ''):
        for this_trait in trait_list:

            if not this_trait.haveinfo:
                this_trait.retrieve_info(get_qtl_info=True)

            description = this_trait.post_publication_description

            #If the dataset is confidential and the user has access to confidential
            #phenotype traits, then display the pre-publication description instead
            #of the post-publication description
            if this_trait.confidential:
                this_trait.description_display = ""
                continue   # for now, because no authorization features

                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(
                        privilege=self.privilege,
                        userName=self.userName,
                        authorized_users=this_trait.authorized_users):

                    description = this_trait.pre_publication_description

            if len(description) > 0:
                this_trait.description_display = description.strip()
            else:
                this_trait.description_display = ""

            if not this_trait.year.isdigit():
                this_trait.pubmed_text = "N/A"
            else:
                this_trait.pubmed_text = this_trait.year

            if this_trait.pubmed_id:
                this_trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id

            #LRS and its location
            this_trait.LRS_score_repr = "N/A"
            this_trait.LRS_location_repr = "N/A"

            if this_trait.lrs:
                query = """
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '%s' and
                        Geno.Name = '%s' and
                        Geno.SpeciesId = Species.Id
                """ % (species, this_trait.locus)
                logger.sql(query)
                result = g.db.execute(query).fetchone()

                if result:
                    if result[0] and result[1]:
                        LRS_Chr = result[0]
                        LRS_Mb = result[1]

                        this_trait.LRS_score_repr = LRS_score_repr = '%3.1f' % this_trait.lrs
                        this_trait.LRS_location_repr = LRS_location_repr = 'Chr%s: %.6f' % (LRS_Chr, float(LRS_Mb))

    def retrieve_sample_data(self, trait):
        query = """
                    SELECT
                            Strain.Name, PublishData.value, PublishSE.error, NStrain.count, Strain.Name2
                    FROM
                            (PublishData, Strain, PublishXRef, PublishFreeze)
                    left join PublishSE on
                            (PublishSE.DataId = PublishData.Id AND PublishSE.StrainId = PublishData.StrainId)
                    left join NStrain on
                            (NStrain.DataId = PublishData.Id AND
                            NStrain.StrainId = PublishData.StrainId)
                    WHERE
                            PublishXRef.InbredSetId = PublishFreeze.InbredSetId AND
                            PublishData.Id = PublishXRef.DataId AND PublishXRef.Id = %s AND
                            PublishFreeze.Id = %s AND PublishData.StrainId = Strain.Id
                    Order BY
                            Strain.Name
                    """
        logger.sql(query)
        results = g.db.execute(query, (trait, self.id)).fetchall()
        return results


class GenotypeDataSet(DataSet):
    DS_NAME_MAP['Geno'] = 'GenotypeDataSet'

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Name',
                              'Chr']

        # Find out what display_fields is
        self.display_fields = ['name',
                               'chr',
                               'mb',
                               'source2',
                               'sequence']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                              'ID',
                              'Location']

        # Todo: Obsolete or rename this field
        self.type = 'Geno'

        self.query_for_group = '''
                SELECT
                        InbredSet.Name, InbredSet.Id, InbredSet.GeneticType
                FROM
                        InbredSet, GenoFreeze
                WHERE
                        GenoFreeze.InbredSetId = InbredSet.Id AND
                        GenoFreeze.Name = "%s"
                ''' % escape(self.name)

    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list, species=None):
        for this_trait in trait_list:
            if not this_trait.haveinfo:
                this_trait.retrieveInfo()

            if this_trait.chr and this_trait.mb:
                this_trait.location_repr = 'Chr%s: %.6f' % (this_trait.chr, float(this_trait.mb) )

    def retrieve_sample_data(self, trait):
        query = """
                    SELECT
                            Strain.Name, GenoData.value, GenoSE.error, GenoData.Id, Strain.Name2
                    FROM
                            (GenoData, GenoFreeze, Strain, Geno, GenoXRef)
                    left join GenoSE on
                            (GenoSE.DataId = GenoData.Id AND GenoSE.StrainId = GenoData.StrainId)
                    WHERE
                            Geno.SpeciesId = %s AND Geno.Name = %s AND GenoXRef.GenoId = Geno.Id AND
                            GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                            GenoFreeze.Name = %s AND
                            GenoXRef.DataId = GenoData.Id AND
                            GenoData.StrainId = Strain.Id
                    Order BY
                            Strain.Name
                    """
        logger.sql(query)
        results = g.db.execute(query,
                               (webqtlDatabaseFunction.retrieve_species_id(self.group.name),
                                trait, self.name)).fetchall()
        return results


class MrnaAssayDataSet(DataSet):
    '''
    An mRNA Assay is a quantitative assessment (assay) associated with an mRNA trait

    This used to be called ProbeSet, but that term only refers specifically to the Affymetrix
    platform and is far too specific.

    '''
    DS_NAME_MAP['ProbeSet'] = 'MrnaAssayDataSet'

    def setup(self):
        # Fields in the database table
        self.search_fields = ['Name',
                              'Description',
                              'Probe_Target_Description',
                              'Symbol',
                              'Alias',
                              'GenbankId',
                              'UniGeneId',
                              'RefSeq_TranscriptId']

        # Find out what display_fields is
        self.display_fields = ['name', 'symbol',
                               'description', 'probe_target_description',
                               'chr', 'mb',
                               'alias', 'geneid',
                               'genbankid', 'unigeneid',
                               'omim', 'refseq_transcriptid',
                               'blatseq', 'targetseq',
                               'chipid', 'comments',
                               'strand_probe', 'strand_gene',
                               'proteinid', 'uniprotid',
                               'probe_set_target_region',
                               'probe_set_specificity',
                               'probe_set_blat_score',
                               'probe_set_blat_mb_start',
                               'probe_set_blat_mb_end',
                               'probe_set_strand',
                               'probe_set_note_by_rw',
                               'flag']

        # Fields displayed in the search results table header
        self.header_fields = ['Index',
                             'Record',
                             'Symbol',
                             'Description',
                             'Location',
                             'Mean',
                             'Max LRS',
                             'Max LRS Location',
                             'Additive Effect']

        # Todo: Obsolete or rename this field
        self.type = 'ProbeSet'

        self.query_for_group = '''
                        SELECT
                                InbredSet.Name, InbredSet.Id, InbredSet.GeneticType
                        FROM
                                InbredSet, ProbeSetFreeze, ProbeFreeze
                        WHERE
                                ProbeFreeze.InbredSetId = InbredSet.Id AND
                                ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND
                                ProbeSetFreeze.Name = "%s"
                ''' % escape(self.name)


    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list=None, species=''):

        #  Note: setting trait_list to [] is probably not a great idea.
        if not trait_list:
            trait_list = []

        for this_trait in trait_list:

            if not this_trait.haveinfo:
                this_trait.retrieveInfo(QTL=1)

            if not this_trait.symbol:
                this_trait.symbol = "N/A"

            #XZ, 12/08/2008: description
            #XZ, 06/05/2009: Rob asked to add probe target description
            description_string = unicode(str(this_trait.description).strip(codecs.BOM_UTF8), 'utf-8')
            target_string = unicode(str(this_trait.probe_target_description).strip(codecs.BOM_UTF8), 'utf-8')

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = this_trait.symbol

            if (len(description_display) > 1 and description_display != 'N/A' and
                    len(target_string) > 1 and target_string != 'None'):
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            this_trait.description_display = description_display

            if this_trait.chr and this_trait.mb:
                this_trait.location_repr = 'Chr%s: %.6f' % (this_trait.chr, float(this_trait.mb))

            #Get mean expression value
            query = (
            """select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
                where ProbeSetXRef.ProbeSetFreezeId = %s and
                ProbeSet.Id = ProbeSetXRef.ProbeSetId and
                ProbeSet.Name = '%s'
            """ % (escape(str(this_trait.dataset.id)),
                   escape(this_trait.name)))

            #logger.debug("query is:", pf(query))
            logger.sql(query)
            result = g.db.execute(query).fetchone()

            mean = result[0] if result else 0

            if mean:
                this_trait.mean = "%2.3f" % mean

            #LRS and its location
            this_trait.LRS_score_repr = 'N/A'
            this_trait.LRS_location_repr = 'N/A'

            #Max LRS and its Locus location
            if this_trait.lrs and this_trait.locus:
                query = """
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '{}' and
                        Geno.Name = '{}' and
                        Geno.SpeciesId = Species.Id
                """.format(species, this_trait.locus)
                logger.sql(query)
                result = g.db.execute(query).fetchone()

                if result:
                    lrs_chr, lrs_mb = result
                    this_trait.LRS_score_repr = '%3.1f' % this_trait.lrs
                    this_trait.LRS_location_repr = 'Chr%s: %.6f' % (lrs_chr, float(lrs_mb))

        return trait_list

    def retrieve_sample_data(self, trait):
        query = """
                    SELECT
                            Strain.Name, ProbeSetData.value, ProbeSetSE.error, ProbeSetData.Id, Strain.Name2
                    FROM
                            (ProbeSetData, ProbeSetFreeze, Strain, ProbeSet, ProbeSetXRef)
                    left join ProbeSetSE on
                            (ProbeSetSE.DataId = ProbeSetData.Id AND ProbeSetSE.StrainId = ProbeSetData.StrainId)
                    WHERE
                            ProbeSet.Name = '%s' AND ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                            ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                            ProbeSetFreeze.Name = '%s' AND
                            ProbeSetXRef.DataId = ProbeSetData.Id AND
                            ProbeSetData.StrainId = Strain.Id
                    Order BY
                            Strain.Name
                    """ % (escape(trait), escape(self.name))
        logger.sql(query)
        results = g.db.execute(query).fetchall()
        #logger.debug("RETRIEVED RESULTS HERE:", results)
        return results

    def retrieve_genes(self, column_name):
        query = """
                    select ProbeSet.Name, ProbeSet.%s
                    from ProbeSet,ProbeSetXRef
                    where ProbeSetXRef.ProbeSetFreezeId = %s and
                    ProbeSetXRef.ProbeSetId=ProbeSet.Id;
                """ % (column_name, escape(str(self.id)))
        logger.sql(query)
        results = g.db.execute(query).fetchall()

        return dict(results)


class TempDataSet(DataSet):
    '''Temporary user-generated data set'''

    DS_NAME_MAP['Temp'] = 'TempDataSet'

    def setup(self):
        self.search_fields = ['name',
                              'description']

        self.display_fields = ['name',
                               'description']

        self.header_fields = ['Name',
                              'Description']

        self.type = 'Temp'

        # Need to double check later how these are used
        self.id = 1
        self.fullname = 'Temporary Storage'
        self.shortname = 'Temp'


    @staticmethod
    def handle_pca(desc):
        if 'PCA' in desc:
            # Todo: Modernize below lines
            desc = desc[desc.rindex(':')+1:].strip()
        else:
            desc = desc[:desc.index('entered')].strip()
        return desc

    def get_desc(self):
        query = 'SELECT description FROM Temp WHERE Name=%s' % self.name
        logger.sql(query)
        g.db.execute(query)
        desc = g.db.fetchone()[0]
        desc = self.handle_pca(desc)
        return desc

    def retrieve_sample_data(self, trait):
        query = """
                SELECT
                        Strain.Name, TempData.value, TempData.SE, TempData.NStrain, TempData.Id
                FROM
                        TempData, Temp, Strain
                WHERE
                        TempData.StrainId = Strain.Id AND
                        TempData.Id = Temp.DataId AND
                        Temp.name = '%s'
                Order BY
                        Strain.Name
                """ % escape(trait.name)

        logger.sql(query)
        results = g.db.execute(query).fetchall()


def geno_mrna_confidentiality(ob):
    dataset_table = ob.type + "Freeze"
    #logger.debug("dataset_table [%s]: %s" % (type(dataset_table), dataset_table))

    query = '''SELECT Id, Name, FullName, confidentiality,
                        AuthorisedUsers FROM %s WHERE Name = "%s"''' % (dataset_table,ob.name)
    logger.sql(query)
    result = g.db.execute(query)

    (dataset_id,
     name,
     full_name,
     confidential,
     authorized_users) = result.fetchall()[0]

    if confidential:
        return True
