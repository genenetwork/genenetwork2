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
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)

from __future__ import print_function, division

from flask import Flask, g

from htmlgen import HTMLgen2 as HT

import webqtlConfig

from MySQLdb import escape_string as escape
from pprint import pformat as pf

# Used by create_database to instantiate objects
DS_NAME_MAP = {}

def create_dataset(dataset_name):
    #cursor = db_conn.cursor()
    print("dataset_name:", dataset_name)

    dataset_type = g.db.execute("""
        SELECT DBType.Name
        FROM DBList, DBType
        WHERE DBList.Name = %s and
              DBType.Id = DBList.DBTypeId
        """, (dataset_name)).fetchone().Name

    #dataset_type = cursor.fetchone()[0]
    print("[blubber] dataset_type:", pf(dataset_type))

    dataset_ob = DS_NAME_MAP[dataset_type]
    #dataset_class = getattr(data_set, dataset_ob)
    print("dataset_ob:", dataset_ob)
    print("DS_NAME_MAP:", pf(DS_NAME_MAP))

    dataset_class = globals()[dataset_ob]
    return dataset_class(dataset_name)


class DataSet(object):
    """
    DataSet class defines a dataset in webqtl, can be either Microarray,
    Published phenotype, genotype, or user input dataset(temp)

    """

    def __init__(self, name):

        assert name
        self.name = name
        self.id = None
        self.type = None
        self.group = None

        self.setup()

        self.check_confidentiality()

        self.retrieve_name()
        self.get_group()


    # Delete this eventually
    @property
    def riset():
        Weve_Renamed_This_As_Group


    def get_group(self):
        self.group, self.group_id = g.db.execute(self.query).fetchone()
        if self.group == 'BXD300':
            self.group = "BXD"
        #return group


    def retrieve_name(self):
        """
        If the data set name parameter is not found in the 'Name' field of the data set table,
        check if it is actually the FullName or ShortName instead.

        This is not meant to retrieve the data set info if no name at all is passed.

        """

        query_args = tuple(escape(x) for x in (
            (self.type + "Freeze"),
            str(webqtlConfig.PUBLICTHRESH),
            self.name,
            self.name,
            self.name))
        print("query_args are:", query_args)

        print("""
                SELECT Id, Name, FullName, ShortName
                FROM %s
                WHERE public > %s AND
                     (Name = '%s' OR FullName = '%s' OR ShortName = '%s')
          """ % (query_args))

        self.id, self.name, self.fullname, self.shortname = g.db.execute("""
                SELECT Id, Name, FullName, ShortName
                FROM %s
                WHERE public > %s AND
                     (Name = '%s' OR FullName = '%s' OR ShortName = '%s')
          """ % (query_args)).fetchone()

        #self.cursor.execute(query)
        #self.id, self.name, self.fullname, self.shortname = self.cursor.fetchone()


    #def genHTML(self, Class='c0dd'):
    #    return  HT.Href(text = HT.Span('%s Database' % self.fullname, Class= "fwb " + Class),
    #            url= webqtlConfig.INFOPAGEHREF % self.name,target="_blank")

class PhenotypeDataSet(DataSet):
    DS_NAME_MAP['Publish'] = 'PhenotypeDataSet'

    def setup(self):
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
        self.display_fields = ['name',
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
        self.header_fields = ['',
                            'ID',
                            'Description',
                            'Authors',
                            'Year',
                            'Max LRS',
                            'Max LRS Location']

        self.type = 'Publish'

        self.query = '''
                            SELECT
                                    InbredSet.Name, InbredSet.Id
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
                this_trait.retrieveInfo(QTL=1)

            description = this_trait.post_publication_description
            if this_trait.confidential:
                continue   # for now
                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
                    description = this_trait.pre_publication_description
            this_trait.description_display = description

            if not this_trait.year.isdigit():
                this_trait.pubmed_text = "N/A"

            if this_trait.pubmed_id:
                this_trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id

            #LRS and its location
            this_trait.LRS_score_repr = "N/A"
            this_trait.LRS_score_value = 0
            this_trait.LRS_location_repr = "N/A"
            this_trait.LRS_location_value = 1000000

            if this_trait.lrs:
                result = g.db.execute("""
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = %s and
                        Geno.Name = %s and
                        Geno.SpeciesId = Species.Id
                """, (species, this_trait.locus)).fetchone()
                #result = self.cursor.fetchone()

                if result:
                    if result[0] and result[1]:
                        LRS_Chr = result[0]
                        LRS_Mb = result[1]

                        #XZ: LRS_location_value is used for sorting
                        try:
                            LRS_location_value = int(LRS_Chr)*1000 + float(LRS_Mb)
                        except:
                            if LRS_Chr.upper() == 'X':
                                LRS_location_value = 20*1000 + float(LRS_Mb)
                            else:
                                LRS_location_value = ord(str(LRS_chr).upper()[0])*1000 + float(LRS_Mb)

                        this_trait.LRS_score_repr = LRS_score_repr = '%3.1f' % this_trait.lrs
                        this_trait.LRS_score_value = LRS_score_value = this_trait.lrs
                        this_trait.LRS_location_repr = LRS_location_repr = 'Chr %s: %.4f Mb' % (LRS_Chr, float(LRS_Mb) )

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
        self.header_fields = ['',
                              'ID',
                              'Location']

        # Todo: Obsolete or rename this field
        self.type = 'Geno'

        self.query = '''
                SELECT
                        InbredSet.Name, InbredSet.Id
                FROM
                        InbredSet, GenoFreeze
                WHERE
                        GenoFreeze.InbredSetId = InbredSet.Id AND
                        GenoFreeze.Name = "%s"
                ''' % self.db_conn.escape_string(self.name)

    def check_confidentiality(self):
        return geno_mrna_confidentiality(self)

    def get_trait_info(self, trait_list, species=None):
        for this_trait in trait_list:
            if not this_trait.haveinfo:
                this_trait.retrieveInfo()

            #XZ: trait_location_value is used for sorting
            trait_location_repr = 'N/A'
            trait_location_value = 1000000

            if this_trait.chr and this_trait.mb:
                try:
                    trait_location_value = int(this_trait.chr)*1000 + this_trait.mb
                except:
                    if this_trait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + this_trait.mb
                    else:
                        trait_location_value = ord(str(this_trait.chr).upper()[0])*1000 + this_trait.mb

                this_trait.location_repr = 'Chr%s: %.4f' % (this_trait.chr, float(this_trait.mb) )
                this_trait.location_value = trait_location_value


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
                               'probe_set_target_region',
                               'probe_set_specificity',
                               'probe_set_blat_score',
                               'probe_set_blat_mb_start',
                               'probe_set_blat_mb_end',
                               'probe_set_strand',
                               'probe_set_note_by_rw',
                               'flag']

        # Fields displayed in the search results table header
        self.header_fields = ['',
                             'ID',
                             'Symbol',
                             'Description',
                             'Location',
                             'Mean Expr',
                             'Max LRS',
                             'Max LRS Location']

        # Todo: Obsolete or rename this field
        self.type = 'ProbeSet'

        self.query = '''
                        SELECT
                                InbredSet.Name, InbredSet.Id
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

            if this_trait.symbol:
                pass
            else:
                this_trait.symbol = "N/A"

            #XZ, 12/08/2008: description
            #XZ, 06/05/2009: Rob asked to add probe target description
            description_string = str(this_trait.description).strip()
            target_string = str(this_trait.probe_target_description).strip()

            description_display = ''

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = this_trait.symbol

            if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                description_display = description_display + '; ' + target_string.strip()

            # Save it for the jinja2 template
            this_trait.description_display = description_display
            #print("  xxxxdd [%s]: %s" % (type(this_trait.description_display), description_display))

            #XZ: trait_location_value is used for sorting
            trait_location_repr = 'N/A'
            trait_location_value = 1000000

            if this_trait.chr and this_trait.mb:
                try:
                    trait_location_value = int(this_trait.chr)*1000 + this_trait.mb
                except:
                    if this_trait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + this_trait.mb
                    else:
                        trait_location_value = ord(str(this_trait.chr).upper()[0])*1000 + this_trait.mb

                this_trait.location_repr = 'Chr %s: %.4f Mb' % (this_trait.chr, float(this_trait.mb) )
                this_trait.location_value = trait_location_value
                #this_trait.trait_location_value = trait_location_value

            #XZ, 01/12/08: This SQL query is much faster.
            query = (
"""select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
    where ProbeSetXRef.ProbeSetFreezeId = %s and
    ProbeSet.Id = ProbeSetXRef.ProbeSetId and
    ProbeSet.Name = '%s'
            """ % (self.db_conn.escape_string(str(this_trait.dataset.id)),
                   self.db_conn.escape_string(this_trait.name)))

            print("query is:", pf(query))

            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if result:
                if result[0]:
                    mean = result[0]
                else:
                    mean=0
            else:
                mean = 0

            #XZ, 06/05/2009: It is neccessary to turn on nowrap
            this_trait.mean = repr = "%2.3f" % mean

            #LRS and its location
            this_trait.LRS_score_repr = 'N/A'
            this_trait.LRS_score_value = 0
            this_trait.LRS_location_repr = 'N/A'
            this_trait.LRS_location_value = 1000000

            #Max LRS and its Locus location
            if this_trait.lrs and this_trait.locus:
                self.cursor.execute("""
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '%s' and
                        Geno.Name = '%s' and
                        Geno.SpeciesId = Species.Id
                """ % (species, this_trait.locus))
                result = self.cursor.fetchone()

                if result:
                    if result[0] and result[1]:
                        LRS_Chr = result[0]
                        LRS_Mb = result[1]

                        #XZ: LRS_location_value is used for sorting
                        try:
                            LRS_location_value = int(LRS_Chr)*1000 + float(LRS_Mb)
                        except:
                            if LRS_Chr.upper() == 'X':
                                LRS_location_value = 20*1000 + float(LRS_Mb)
                            else:
                                LRS_location_value = ord(str(LRS_chr).upper()[0])*1000 + float(LRS_Mb)

                        this_trait.LRS_score_repr = LRS_score_repr = '%3.1f' % this_trait.lrs
                        this_trait.LRS_score_value = LRS_score_value = this_trait.lrs
                        this_trait.LRS_location_repr = LRS_location_repr = 'Chr %s: %.4f Mb' % (LRS_Chr, float(LRS_Mb) )


class TempDataSet(DataSet):
    '''Temporary user-generated data set'''

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


def geno_mrna_confidentiality(ob):
    dataset_table = ob.type + "Freeze"
    print("dataset_table [%s]: %s" % (type(dataset_table), dataset_table))

    query = '''SELECT Id, Name, FullName, confidentiality,
                        AuthorisedUsers FROM %s WHERE Name = %%s''' % (dataset_table)

    result = g.db.execute(query, ob.name)

    (dataset_id,
     name,
     full_name,
     confidential,
     authorized_users) = result.fetchall()[0]

    if confidential:
        # Allow confidential data later
        NoConfindetialDataForYouTodaySorry
