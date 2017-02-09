from __future__ import absolute_import, print_function, division

import string
import os
import cPickle
import uuid
import json as json
#import pyXLWriter as xl

from collections import OrderedDict

from flask import Flask, g

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base import webqtlCaseData
from wqflask.show_trait.SampleList import SampleList
from utility import webqtlUtil, Plot, Bunch, helper_functions
from base.trait import GeneralTrait
from base import data_set
from db import webqtlDatabaseFunction
from basicStatistics import BasicStatisticsFunctions

from pprint import pformat as pf

from utility.tools import flat_files, flat_file_exists
from utility.tools import get_setting

from utility.logger import getLogger
logger = getLogger(__name__ )

###############################################
#
# Todo: Put in security to ensure that user has permission to access confidential data sets
# And add i.p.limiting as necessary
#
##############################################

class ShowTrait(object):

    def __init__(self, kw):
        logger.debug("in ShowTrait, kw are:", kw)

        if kw['trait_id'] != None:
            self.temp_trait = False
            self.trait_id = kw['trait_id']
            helper_functions.get_species_dataset_trait(self, kw)
        else:
            self.temp_trait = True
            self.trait_vals = kw['trait_paste'].split()
            self.temp_group = kw['group']
            self.temp_species = kw['species']
            #self.create_temp_trait()

        #self.dataset.group.read_genotype_file()

        #if this_trait:
        #    if this_trait.dataset and this_trait.dataset.type and this_trait.dataset.type == 'ProbeSet':
        #            self.cursor.execute("SELECT h2 from ProbeSetXRef WHERE DataId = %d" %
        #                                this_trait.mysqlid)
        #            heritability = self.cursor.fetchone()

        self.build_correlation_tools()

        #Get nearest marker for composite mapping

        if hasattr(self.this_trait, 'locus_chr') and self.this_trait.locus_chr != "" and self.dataset.type != "Geno" and self.dataset.type != "Publish":
            self.nearest_marker = get_nearest_marker(self.this_trait, self.dataset)
            #self.nearest_marker1 = get_nearest_marker(self.this_trait, self.dataset)[0]
            #self.nearest_marker2 = get_nearest_marker(self.this_trait, self.dataset)[1]
        else:
            self.nearest_marker = ""
            #self.nearest_marker1 = ""
            #self.nearest_marker2 = ""

        self.make_sample_lists(self.this_trait)

        # Todo: Add back in the ones we actually need from below, as we discover we need them
        hddn = OrderedDict()

        if self.dataset.group.allsamples:
            hddn['allsamples'] = string.join(self.dataset.group.allsamples, ' ')

        hddn['trait_id'] = self.trait_id
        hddn['dataset'] = self.dataset.name
        hddn['use_outliers'] = False
        hddn['method'] = "pylmm"
        hddn['mapping_display_all'] = True
        hddn['suggestive'] = 0
        hddn['num_perm'] = 0
        hddn['manhattan_plot'] = ""
        if hasattr(self.this_trait, 'locus_chr') and self.this_trait.locus_chr != "" and self.dataset.type != "Geno" and self.dataset.type != "Publish":
            hddn['control_marker'] = self.nearest_marker
            #hddn['control_marker'] = self.nearest_marker1+","+self.nearest_marker2
        else:
            hddn['control_marker'] = ""
        hddn['do_control'] = False
        hddn['maf'] = 0.01
        hddn['compare_traits'] = []
        hddn['export_data'] = ""

        # We'll need access to this_trait and hddn in the Jinja2 Template, so we put it inside self
        self.hddn = hddn

        self.temp_uuid = uuid.uuid4()

        self.sample_group_types = OrderedDict()
        if len(self.sample_groups) > 1:
            self.sample_group_types['samples_primary'] = self.dataset.group.name + " Only"
            self.sample_group_types['samples_other'] = "Non-" + self.dataset.group.name
            self.sample_group_types['samples_all'] = "All Cases"
        else:
            self.sample_group_types['samples_primary'] = self.dataset.group.name
        sample_lists = [group.sample_list for group in self.sample_groups]

        self.get_mapping_methods()

        self.trait_table_width = get_trait_table_width(self.sample_groups)

        if self.this_trait.symbol:
            trait_symbol = self.this_trait.symbol
        else:
            trait_symbol = None
        js_data = dict(trait_id = self.this_trait.name,
                       trait_symbol = trait_symbol,
                       dataset_type = self.dataset.type,
                       data_scale = self.dataset.data_scale,
                       sample_group_types = self.sample_group_types,
                       sample_lists = sample_lists,
                       attribute_names = self.sample_groups[0].attributes,
                       temp_uuid = self.temp_uuid)
        self.js_data = js_data

    def get_mapping_methods(self):
        '''Only display mapping methods when the dataset group's genotype file exists'''
        def check_plink_gemma():
            if flat_file_exists("mapping"):
                MAPPING_PATH = flat_files("mapping")+"/"
                if (os.path.isfile(MAPPING_PATH+self.dataset.group.name+".bed") and
                    (os.path.isfile(MAPPING_PATH+self.dataset.group.name+".map") or
                     os.path.isfile(MAPPING_PATH+self.dataset.group.name+".bim"))):
                    return True
            return False

        def check_pylmm_rqtl():
            if os.path.isfile(webqtlConfig.GENODIR+self.dataset.group.name+".geno") and (os.path.getsize(webqtlConfig.JSON_GENODIR+self.dataset.group.name+".json") > 0):
                return True
            else:
                return False

        self.genofiles = get_genofiles(self.this_trait)
        self.use_plink_gemma = check_plink_gemma()
        self.use_pylmm_rqtl = check_pylmm_rqtl()


    def build_correlation_tools(self):
        if self.temp_trait == True:
            this_group = self.temp_group
        else:
            this_group = self.dataset.group.name

        # We're checking a string here!
        assert isinstance(this_group, basestring), "We need a string type thing here"
        if this_group[:3] == 'BXD':
            this_group = 'BXD'

        if this_group:
            #dataset_menu = self.dataset.group.datasets()
            if self.temp_trait == True:
                dataset_menu = data_set.datasets(this_group)
            else:
                dataset_menu = data_set.datasets(this_group, self.dataset.group)
            dataset_menu_selected = None
            if len(dataset_menu):
                if self.this_trait and self.this_trait.dataset:
                    dataset_menu_selected = self.this_trait.dataset.name

                return_results_menu = (100, 200, 500, 1000, 2000, 5000, 10000, 15000, 20000)
                return_results_menu_selected = 500

            self.corr_tools = dict(dataset_menu = dataset_menu,
                                          dataset_menu_selected = dataset_menu_selected,
                                          return_results_menu = return_results_menu,
                                          return_results_menu_selected = return_results_menu_selected,)


    def make_sample_lists(self, this_trait):
        all_samples_ordered = self.dataset.group.all_samples_ordered()
        
        primary_sample_names = list(all_samples_ordered)

        other_sample_names = []
        for sample in this_trait.data.keys():
            if (this_trait.data[sample].name2 in primary_sample_names) and (this_trait.data[sample].name not in primary_sample_names):
                primary_sample_names.append(this_trait.data[sample].name)
                primary_sample_names.remove(this_trait.data[sample].name2)
            elif sample not in all_samples_ordered:
                all_samples_ordered.append(sample)
                other_sample_names.append(sample)

        if self.dataset.group.species == "human":
            primary_sample_names += other_sample_names

        primary_samples = SampleList(dataset = self.dataset,
                                        sample_names=primary_sample_names,
                                        this_trait=this_trait,
                                        sample_group_type='primary',
                                        header="%s Only" % (self.dataset.group.name))
        logger.debug("primary_samples is: ", pf(primary_samples))

        logger.debug("other_sample_names2:", other_sample_names)
        if other_sample_names and self.dataset.group.species != "human" and self.dataset.group.name != "CFW":
            parent_f1_samples = None
            if self.dataset.group.parlist and self.dataset.group.f1list:
                parent_f1_samples = self.dataset.group.parlist + self.dataset.group.f1list

            other_sample_names.sort() #Sort other samples
            if parent_f1_samples:
                other_sample_names = parent_f1_samples + other_sample_names

            logger.debug("other_sample_names:", other_sample_names)

            other_samples = SampleList(dataset=self.dataset,
                                        sample_names=other_sample_names,
                                        this_trait=this_trait,
                                        sample_group_type='other',
                                        header="Non-%s" % (self.dataset.group.name))

            self.sample_groups = (primary_samples, other_samples)
        else:
            self.sample_groups = (primary_samples,)

        #TODO: Figure out why this if statement is written this way - Zach
        #if (other_sample_names or (fd.f1list and this_trait.data.has_key(fd.f1list[0]))
        #        or (fd.f1list and this_trait.data.has_key(fd.f1list[1]))):
        #    logger.debug("hjs")
        self.dataset.group.allsamples = all_samples_ordered

def get_nearest_marker(this_trait, this_db):
    this_chr = this_trait.locus_chr
    logger.debug("this_chr:", this_chr)
    this_mb = this_trait.locus_mb
    logger.debug("this_mb:", this_mb)
    #One option is to take flanking markers, another is to take the two (or one) closest
    query = """SELECT Geno.Name
               FROM Geno, GenoXRef, GenoFreeze
               WHERE Geno.Chr = '{}' AND
                     GenoXRef.GenoId = Geno.Id AND
                     GenoFreeze.Id = GenoXRef.GenoFreezeId AND
                     GenoFreeze.Name = '{}'
               ORDER BY ABS( Geno.Mb - {}) LIMIT 1""".format(this_chr, this_db.group.name+"Geno", this_mb)
    logger.sql(query)
    result = g.db.execute(query).fetchall()
    logger.debug("result:", result)

    if result == []:
        return ""
        #return "", ""
    else:
        return result[0][0]
        #return result[0][0], result[1][0]

def get_genofiles(this_trait):
    jsonfile = "%s/%s.json" % (webqtlConfig.GENODIR, this_trait.dataset.group.name)
    try:
        f = open(jsonfile)
    except:
        return None
    jsondata = json.load(f)
    return jsondata['genofile']

def get_trait_table_width(sample_groups):
    table_width = 20
    if sample_groups[0].se_exists():
        table_width += 15
    if (table_width + len(sample_groups[0].attributes)*10) > 100:
        table_width = 100
    else:
        table_width += len(sample_groups[0].attributes)*10

    return table_width
