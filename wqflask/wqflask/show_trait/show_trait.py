from __future__ import absolute_import, print_function, division

import string
import os
import datetime
import cPickle
import uuid
import json as json

from collections import OrderedDict

import redis
Redis = redis.StrictRedis()

import numpy as np
import scipy.stats as ss

from flask import Flask, g

from base import webqtlConfig
from base import webqtlCaseData
from wqflask.show_trait.SampleList import SampleList
from utility import webqtlUtil, Plot, Bunch, helper_functions
from base.trait import GeneralTrait
from base import data_set
from db import webqtlDatabaseFunction

from pprint import pformat as pf

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

        if 'trait_id' in kw and kw['dataset'] != "Temp":
            self.temp_trait = False
            self.trait_id = kw['trait_id']
            helper_functions.get_species_dataset_trait(self, kw)
        elif 'group' in kw:
            self.temp_trait = True
            self.trait_id = "Temp_"+kw['species']+ "_" + kw['group'] + "_" + datetime.datetime.now().strftime("%m%d%H%M%S")
            self.temp_species = kw['species']
            self.temp_group = kw['group']
            self.dataset = data_set.create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = self.temp_group)
            # Put values in Redis so they can be looked up later if added to a collection
            Redis.set(self.trait_id, kw['trait_paste'])
            self.trait_vals = kw['trait_paste'].split()
            self.this_trait = GeneralTrait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)
        else:
            self.temp_trait = True
            self.trait_id = kw['trait_id']
            self.temp_species = self.trait_id.split("_")[1]
            self.temp_group = self.trait_id.split("_")[2]
            self.dataset = data_set.create_dataset(dataset_name = "Temp", dataset_type = "Temp", group_name = self.temp_group)
            self.this_trait = GeneralTrait(dataset=self.dataset,
                                           name=self.trait_id,
                                           cellid=None)
            self.trait_vals = Redis.get(self.trait_id).split()

        #ZS: Get verify/rna-seq link URLs
        try:
            blatsequence = self.this_trait.blatseq
            if not blatsequence:
                #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
                query1 = """SELECT Probe.Sequence, Probe.Name
                           FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                           WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                 ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                 ProbeSetFreeze.Name = '%s' AND
                                 ProbeSet.Name = '%s' AND
                                 Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (self.this_trait.dataset.name, self.this_trait.name)
                seqs = g.db.execute(query1).fetchall()
                if not seqs:
                    raise ValueError
                else:
                    blatsequence = ''
                    for seqt in seqs:
                        if int(seqt[1][-1]) % 2 == 1:
                            blatsequence += string.strip(seqt[0])

            #--------Hongqiang add this part in order to not only blat ProbeSet, but also blat Probe
            blatsequence = '%3E' + self.this_trait.name + '%0A' + blatsequence + '%0A'
            #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
            query2 = """SELECT Probe.Sequence, Probe.Name
                        FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                        WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                              ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                              ProbeSetFreeze.Name = '%s' AND
                              ProbeSet.Name = '%s' AND
                              Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (self.this_trait.dataset.name, self.this_trait.name)

            seqs = g.db.execute(query2).fetchall()
            for seqt in seqs:
                if int(seqt[1][-1]) %2 == 1:
                    blatsequence += '%3EProbe_' + string.strip(seqt[1]) + '%0A' + string.strip(seqt[0]) + '%0A'

            if self.dataset.group.species == "rat":
                self.UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('rat', 'rn6', blatsequence)
                self.UTHSC_BLAT_URL = ""
            elif self.dataset.group.species == "mouse":
                self.UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('mouse', 'mm10', blatsequence)
                self.UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('mouse', 'mm10', blatsequence)
            elif self.dataset.group.species == "human":
                self.UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('human', 'hg38', blatsequence)
                self.UTHSC_BLAT_URL = ""
            else:
                self.UCSC_BLAT_URL = ""
                self.UTHSC_BLAT_URL = ""
        except:
            self.UCSC_BLAT_URL = ""
            self.UTHSC_BLAT_URL = ""

        if self.dataset.type == "ProbeSet":
            self.show_probes = "True"

        trait_units = get_trait_units(self.this_trait)
        self.get_external_links()
        self.build_correlation_tools()

        #Get nearest marker for composite mapping
        if not self.temp_trait:
            if check_if_attr_exists(self.this_trait, 'locus_chr') and self.dataset.type != "Geno" and self.dataset.type != "Publish":
                self.nearest_marker = get_nearest_marker(self.this_trait, self.dataset)
                #self.nearest_marker1 = get_nearest_marker(self.this_trait, self.dataset)[0]
                #self.nearest_marker2 = get_nearest_marker(self.this_trait, self.dataset)[1]
            else:
                self.nearest_marker = ""
                #self.nearest_marker1 = ""
                #self.nearest_marker2 = ""

        self.make_sample_lists()

        self.qnorm_vals = quantile_normalize_vals(self.sample_groups)
        self.z_scores = get_z_scores(self.sample_groups)

        self.temp_uuid = uuid.uuid4()

        self.sample_group_types = OrderedDict()
        if len(self.sample_groups) > 1:
            self.sample_group_types['samples_primary'] = self.dataset.group.name
            self.sample_group_types['samples_other'] = "Other"
            self.sample_group_types['samples_all'] = "All"
        else:
            self.sample_group_types['samples_primary'] = self.dataset.group.name
        sample_lists = [group.sample_list for group in self.sample_groups]

        #ZS: Get list of chromosomes to select for mapping
        self.chr_list = [["All", -1]]
        for i, this_chr in enumerate(self.dataset.species.chromosomes.chromosomes):
            self.chr_list.append([self.dataset.species.chromosomes.chromosomes[this_chr].name, i])

        self.genofiles = get_genofiles(self.dataset)

        self.has_num_cases = has_num_cases(self.this_trait)

        self.stats_table_width, self.trait_table_width = get_table_widths(self.sample_groups, self.has_num_cases)

        #ZS: Needed to know whether to display bar chart + get max sample name length in order to set table column width
        self.num_values = 0
        self.binary = "true" #ZS: So it knows whether to display the Binary R/qtl mapping method, which doesn't work unless all values are 0 or 1
        self.negative_vals_exist = "false" #ZS: Since we don't want to show log2 transform option for situations where it doesn't make sense
        max_samplename_width = 1
        for group in self.sample_groups:
            for sample in group.sample_list:
                if len(sample.name) > max_samplename_width:
                    max_samplename_width = len(sample.name)
                if sample.display_value != "x":
                    self.num_values += 1
                    if sample.display_value != 0 or sample.display_value != 1:
                        self.binary = "false"
                    if sample.value < 0:
                        self.negative_vals_exist = "true"

        sample_column_width = max_samplename_width * 8

        if self.num_values >= 5000:
            self.maf = 0.01
        else:
            self.maf = 0.05

        trait_symbol = None
        short_description = None
        if not self.temp_trait:
            if self.this_trait.symbol:
                trait_symbol = self.this_trait.symbol
                short_description = trait_symbol

            elif hasattr(self.this_trait, 'post_publication_abbreviation'):
                short_description = self.this_trait.post_publication_abbreviation

            elif hasattr(self.this_trait, 'pre_publication_abbreviation'):
                short_description = self.this_trait.pre_publication_abbreviation

        # Todo: Add back in the ones we actually need from below, as we discover we need them
        hddn = OrderedDict()

        if self.dataset.group.allsamples:
            hddn['allsamples'] = string.join(self.dataset.group.allsamples, ' ')
        hddn['primary_samples'] = string.join(self.primary_sample_names, ',')
        hddn['trait_id'] = self.trait_id
        hddn['dataset'] = self.dataset.name
        hddn['temp_trait'] = False
        if self.temp_trait:
           hddn['temp_trait'] = True
           hddn['group'] = self.temp_group
           hddn['species'] = self.temp_species
        hddn['use_outliers'] = False
        hddn['method'] = "gemma"
        hddn['selected_chr'] = -1
        hddn['mapping_display_all'] = True
        hddn['suggestive'] = 0
        hddn['num_perm'] = 0
        hddn['manhattan_plot'] = ""
        hddn['control_marker'] = ""
        if not self.temp_trait:
            if hasattr(self.this_trait, 'locus_chr') and self.this_trait.locus_chr != "" and self.dataset.type != "Geno" and self.dataset.type != "Publish":
                hddn['control_marker'] = self.nearest_marker
                #hddn['control_marker'] = self.nearest_marker1+","+self.nearest_marker2
        hddn['do_control'] = False
        hddn['maf'] = 0.05
        hddn['compare_traits'] = []
        hddn['export_data'] = ""
        hddn['export_format'] = "excel"

        # We'll need access to this_trait and hddn in the Jinja2 Template, so we put it inside self
        self.hddn = hddn

        js_data = dict(trait_id = self.trait_id,
                       trait_symbol = trait_symbol,
                       short_description = short_description,
                       unit_type = trait_units,
                       dataset_type = self.dataset.type,
                       data_scale = self.dataset.data_scale,
                       sample_group_types = self.sample_group_types,
                       sample_lists = sample_lists,
                       attribute_names = self.sample_groups[0].attributes,
                       num_values = self.num_values,
                       qnorm_values = self.qnorm_vals,
                       zscore_values = self.z_scores,
                       sample_column_width = sample_column_width,
                       temp_uuid = self.temp_uuid)
        self.js_data = js_data

    def get_external_links(self):
        #ZS: There's some weirdness here because some fields don't exist while others are empty strings
        self.pubmed_link = webqtlConfig.PUBMEDLINK_URL % self.this_trait.pubmed_id if check_if_attr_exists(self.this_trait, 'pubmed_id') else None
        self.ncbi_gene_link = webqtlConfig.NCBI_LOCUSID % self.this_trait.geneid if check_if_attr_exists(self.this_trait, 'geneid') else None
        self.omim_link = webqtlConfig.OMIM_ID % self.this_trait.omim if check_if_attr_exists(self.this_trait, 'omim') else None
        self.homologene_link = webqtlConfig.HOMOLOGENE_ID % self.this_trait.homologeneid if check_if_attr_exists(self.this_trait, 'homologeneid') else None

        self.genbank_link = None
        if check_if_attr_exists(self.this_trait, 'genbankid'):
            genbank_id = '|'.join(self.this_trait.genbankid.split('|')[0:10])
            if genbank_id[-1] == '|':
                genbank_id = genbank_id[0:-1]
            self.genbank_link = webqtlConfig.GENBANK_ID % genbank_id

        self.uniprot_link = None
        if check_if_attr_exists(self.this_trait, 'uniprotid'):
            self.uniprot_link = webqtlConfig.UNIPROT_URL % self.this_trait.uniprotid

        self.genotation_link = self.gtex_link = self.genebridge_link = self.ucsc_blat_link = self.biogps_link = self.protein_atlas_link = None
        self.string_link = self.panther_link = self.aba_link = self.ebi_gwas_link = self.wiki_pi_link = self.genemania_link = self.ensembl_link = None
        if self.this_trait.symbol:
            self.genotation_link = webqtlConfig.GENOTATION_URL % self.this_trait.symbol
            self.gtex_link = webqtlConfig.GTEX_URL % self.this_trait.symbol
            self.string_link = webqtlConfig.STRING_URL % self.this_trait.symbol
            self.panther_link = webqtlConfig.PANTHER_URL % self.this_trait.symbol
            self.ebi_gwas_link = webqtlConfig.EBIGWAS_URL % self.this_trait.symbol
            self.protein_atlas_link = webqtlConfig.PROTEIN_ATLAS_URL % self.this_trait.symbol
            #self.open_targets_link = webqtlConfig.OPEN_TARGETS_URL % self.this_trait.symbol

            if self.dataset.group.species == "mouse" or self.dataset.group.species == "human":
                if self.dataset.group.species == "mouse":
                    self.genemania_link = webqtlConfig.GENEMANIA_URL % ("mus-musculus", self.this_trait.symbol)
                else:
                    self.genemania_link = webqtlConfig.GENEMANIA_URL % ("homo-sapiens", self.this_trait.symbol)

                if self.dataset.group.species == "mouse":
                    self.aba_link = webqtlConfig.ABA_URL % self.this_trait.symbol

                    query = """SELECT chromosome, txStart, txEnd
                            FROM GeneList
                            WHERE geneSymbol = '{}'""".format(self.this_trait.symbol)

                    results = g.db.execute(query).fetchone()
                    if results:
                        chr, transcript_start, transcript_end = results
                    else:
                        chr = transcript_start = transcript_end = None

                    if chr and transcript_start and transcript_end and self.this_trait.refseq_transcriptid:
                        transcript_start = int(transcript_start*1000000)
                        transcript_end = int(transcript_end*1000000)
                        self.ucsc_blat_link = webqtlConfig.UCSC_REFSEQ % ('mm10', self.this_trait.refseq_transcriptid, chr, transcript_start, transcript_end)

            if self.dataset.group.species == "rat":
                self.genemania_link = webqtlConfig.GENEMANIA_URL % ("rattus-norvegicus", self.this_trait.symbol)

                query = """SELECT kgID, chromosome, txStart, txEnd
                        FROM GeneList_rn33
                        WHERE geneSymbol = '{}'""".format(self.this_trait.symbol)

                results = g.db.execute(query).fetchone()
                if results:
                    kgId, chr, transcript_start, transcript_end = results
                else:
                    kgId = chr = transcript_start = transcript_end = None

                if chr and transcript_start and transcript_end and kgId:
                    transcript_start = int(transcript_start*1000000) # Convert to bases from megabases
                    transcript_end = int(transcript_end*1000000)
                    self.ucsc_blat_link = webqtlConfig.UCSC_REFSEQ % ('rn6', kgId, chr, transcript_start, transcript_end)

            if self.this_trait.geneid and (self.dataset.group.species == "mouse" or self.dataset.group.species == "rat" or self.dataset.group.species == "human"):
                self.biogps_link = webqtlConfig.BIOGPS_URL % (self.dataset.group.species, self.this_trait.geneid)
                self.gemma_link = webqtlConfig.GEMMA_URL % self.this_trait.geneid

                if self.dataset.group.species == "human":
                    self.aba_link = webqtlConfig.ABA_URL % self.this_trait.geneid

    def build_correlation_tools(self):
        if self.temp_trait == True:
            this_group = self.temp_group
        else:
            this_group = self.dataset.group.name

        # We're checking a string here!
        assert isinstance(this_group, basestring), "We need a string type thing here"
        if this_group[:3] == 'BXD' and this_group != "BXD-Harvested":
            this_group = 'BXD'

        if this_group:
            if self.temp_trait == True:
                dataset_menu = data_set.datasets(this_group)
            else:
                dataset_menu = data_set.datasets(this_group, self.dataset.group)
            dataset_menu_selected = None
            if len(dataset_menu):
                if self.dataset:
                    dataset_menu_selected = self.dataset.name

                return_results_menu = (100, 200, 500, 1000, 2000, 5000, 10000, 15000, 20000)
                return_results_menu_selected = 500

            self.corr_tools = dict(dataset_menu = dataset_menu,
                                          dataset_menu_selected = dataset_menu_selected,
                                          return_results_menu = return_results_menu,
                                          return_results_menu_selected = return_results_menu_selected,)

    def make_sample_lists(self):
        all_samples_ordered = self.dataset.group.all_samples_ordered()
        
        parent_f1_samples = []
        if self.dataset.group.parlist and self.dataset.group.f1list:
            parent_f1_samples = self.dataset.group.parlist + self.dataset.group.f1list

        primary_sample_names = list(all_samples_ordered)

        if not self.temp_trait:
            other_sample_names = []
            for sample in self.this_trait.data.keys():
                if (self.this_trait.data[sample].name2 in primary_sample_names) and (self.this_trait.data[sample].name not in primary_sample_names):
                    primary_sample_names.append(self.this_trait.data[sample].name)
                    primary_sample_names.remove(self.this_trait.data[sample].name2)
                elif sample not in all_samples_ordered:
                    all_samples_ordered.append(sample)
                    other_sample_names.append(sample)

            #ZS: CFW is here because the .geno file doesn't properly contain its full list of samples. This should probably be fixed.
            if self.dataset.group.species == "human" or (set(primary_sample_names) == set(parent_f1_samples)) or self.dataset.group.name == "CFW":
                primary_sample_names += other_sample_names
                other_sample_names = []

            if other_sample_names:
                primary_header = "%s Only" % (self.dataset.group.name)
            else:
                primary_header = "Samples"
            primary_samples = SampleList(dataset = self.dataset,
                                            sample_names=primary_sample_names,
                                            this_trait=self.this_trait,
                                            sample_group_type='primary',
                                            header=primary_header)

            #if other_sample_names and self.dataset.group.species != "human" and self.dataset.group.name != "CFW":
            if len(other_sample_names) > 0:
                other_sample_names.sort() #Sort other samples
                if parent_f1_samples:
                    other_sample_names = parent_f1_samples + other_sample_names

                other_samples = SampleList(dataset=self.dataset,
                                            sample_names=other_sample_names,
                                            this_trait=self.this_trait,
                                            sample_group_type='other',
                                            header="Other")

                self.sample_groups = (primary_samples, other_samples)
            else:
                self.sample_groups = (primary_samples,)
        else:
            primary_samples = SampleList(dataset = self.dataset,
                                            sample_names=primary_sample_names,
                                            this_trait=self.trait_vals,
                                            sample_group_type='primary',
                                            header="%s Only" % (self.dataset.group.name))
            self.sample_groups = (primary_samples,)

        self.primary_sample_names = primary_sample_names
        self.dataset.group.allsamples = all_samples_ordered

def quantile_normalize_vals(sample_groups):
    def normf(trait_vals):
        ranked_vals = ss.rankdata(trait_vals)
        p_list = []
        for i, val in enumerate(trait_vals):
            p_list.append(((i+1) - 0.5)/len(trait_vals))

        z = ss.norm.ppf(p_list)

        normed_vals = []
        for rank in ranked_vals:
            normed_vals.append("%0.3f" % z[int(rank)-1])

        return normed_vals

    qnorm_by_group = []
    for sample_type in sample_groups:
        trait_vals = []
        for sample in sample_type.sample_list:
            try:
                trait_vals.append(float(sample.value))
            except:
                continue

        qnorm_vals = normf(trait_vals)
        qnorm_vals_with_x = []
        counter = 0
        for sample in sample_type.sample_list:
            if sample.display_value == "x":
                qnorm_vals_with_x.append("x")
            else:
                qnorm_vals_with_x.append(qnorm_vals[counter])
                counter += 1

        qnorm_by_group.append(qnorm_vals_with_x)

    return qnorm_by_group

def get_z_scores(sample_groups):
    zscore_by_group = []
    for sample_type in sample_groups:
        trait_vals = []
        for sample in sample_type.sample_list:
            try:
                trait_vals.append(float(sample.value))
            except:
                continue

        zscores = ss.mstats.zscore(np.array(trait_vals)).tolist()
        zscores_with_x = []
        counter = 0
        for sample in sample_type.sample_list:
            if sample.display_value == "x":
                zscores_with_x.append("x")
            else:
                zscores_with_x.append("%0.3f" % zscores[counter])
                counter += 1

        zscore_by_group.append(zscores_with_x)

    return zscore_by_group

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

def get_genofiles(this_dataset):
    jsonfile = "%s/%s.json" % (webqtlConfig.GENODIR, this_dataset.group.name)
    try:
        f = open(jsonfile)
    except:
        return None
    jsondata = json.load(f)
    return jsondata['genofile']

def get_table_widths(sample_groups, has_num_cases=False):
    stats_table_width = 250
    if len(sample_groups) > 1:
        stats_table_width = 450

    trait_table_width = 380
    if sample_groups[0].se_exists():
        trait_table_width += 70
    if has_num_cases:
        trait_table_width += 30
    trait_table_width += len(sample_groups[0].attributes)*70

    trait_table_width = str(trait_table_width) + "px"

    return stats_table_width, trait_table_width

def has_num_cases(this_trait):
    has_n = False
    if this_trait.dataset.type != "ProbeSet" and this_trait.dataset.type != "Geno":
        for name, sample in this_trait.data.iteritems():
            if sample.num_cases:
                has_n = True
                break

    return has_n

def get_trait_units(this_trait):
    unit_type = ""
    inside_brackets = False
    if this_trait.description_fmt:
        if ("[" in this_trait.description_fmt) and ("]" in this_trait.description_fmt):
            for i in this_trait.description_fmt:
                if inside_brackets:
                    if i != "]":
                        unit_type += i
                    else:
                        inside_brackets = False
                if i == "[":
                    inside_brackets = True

    if unit_type == "":
        unit_type = "Value"

    return unit_type

def check_if_attr_exists(the_trait, id_type):
    if hasattr(the_trait, id_type):
        if getattr(the_trait, id_type) == None or getattr(the_trait, id_type) == "":
            return False
        else:
            return True
    else:
        return False