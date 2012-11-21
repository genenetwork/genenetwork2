from __future__ import absolute_import, division, print_function

from wqflask import app

from flask import render_template

###################################################
#                                                 #
# This file uses only spaces for indentation      #
#                                                 #
###################################################

import string
import os
import cPickle
import re
from math import *
import time
#import pyXLWriter as xl
#import pp - Note from Sam: is this used?
import math
import datetime

from pprint import pformat as pf

# Instead of importing HT we're going to build a class below until we can eliminate it
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.webqtlDataset import webqtlDataset
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from wqflask import parser
from wqflask import do_search
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction

from utility import formatting

#from base.JinjaPage import JinjaEnv, JinjaPage


class SearchResultPage(templatePage):

    maxReturn = 3000
    nkeywords = 0

    def __init__(self, fd):
        print("initing SearchResultPage")
        import logging_tree
        logging_tree.printout()
        self.fd = fd
        templatePage.__init__(self, fd)
        assert self.openMysql(), "Couldn't open MySQL"

        print("fd is:", pf(fd))
        self.dataset = fd['dataset']

        # change back to self.dataset
        if not self.dataset or self.dataset == 'spacer':
            #Error, No dataset selected
            heading = "Search Result"
            detail = ['''No dataset was selected for this search, please
                go back and SELECT at least one dataset.''']
            self.error(heading=heading,detail=detail,error="No dataset Selected")
            return

        ###########################################
        #   Names and IDs of RISet / F2 set
        ###########################################
        if self.dataset == "All Phenotypes":
            self.cursor.execute("""
                select PublishFreeze.Name, InbredSet.Name, InbredSet.Id from PublishFreeze,
                InbredSet where PublishFreeze.Name not like 'BXD300%' and InbredSet.Id =
                PublishFreeze.InbredSetId""")
            results = self.cursor.fetchall()
            self.dataset = map(lambda x: webqtlDataset(x[0], self.cursor), results)
            self.dataset_groups = map(lambda x: x[1], results)
            self.dataset_group_ids = map(lambda x: x[2], results)
            self.single_group = False
        else:
            print("self.dataset is:", pf(self.dataset))
            self.dataset = webqtlDataset(self.dataset, self.cursor)
            print("self.dataset is now:", pf(self.dataset))
            #self.dataset = map(lambda x: webqtlDataset(x, self.cursor), self.dataset)
            #currently, webqtl won't allow multiple crosses
            #for other than multiple publish db search
            #so we can use the first dataset as example
            #if self.dataset.type=="Publish":
            #    pass
            if self.dataset.type in ("Geno", "ProbeSet"):

                #userExist = None
                # Can't use paramater substitution for table names apparently
                db_type = self.dataset.type + "Freeze"
                print("db_type [%s]: %s" % (type(db_type), db_type))

                query = '''SELECT Id, Name, FullName, confidentiality,
                                    AuthorisedUsers FROM %s WHERE Name = %%s''' % (db_type)

                self.cursor.execute(query, self.dataset.name)

                (indId,
                 indName,
                 indFullName,
                 confidential,
                 AuthorisedUsers) = self.cursor.fetchall()[0]

                if confidential:
                    # Allow confidential data later
                    NoConfindetialDataForYouTodaySorry
                    #access_to_confidential_dataset = 0
                    #
                    ##for the dataset that confidentiality is 1
                    ##1. 'admin' and 'root' can see all of the dataset
                    ##2. 'user' can see the dataset that AuthorisedUsers contains his id(stored in the Id field of User table)
                    #if webqtlConfig.USERDICT[self.privilege] > webqtlConfig.USERDICT['user']:
                    #    access_to_confidential_dataset = 1
                    #else:
                    #    AuthorisedUsersList=AuthorisedUsers.split(',')
                    #    if AuthorisedUsersList.__contains__(self.userName):
                    #        access_to_confidential_dataset = 1
                    #
                    #if not access_to_confidential_dataset:
                    #    #Error, No dataset selected
                    #    heading = "Search Result"
                    #    detail = ["The %s dataset you selected is not open to the public at this time, please go back and SELECT other dataset." % indFullName]
                    #    self.error(heading=heading,detail=detail,error="Confidential dataset")
                    #    return
            #else:
            #    heading = "Search Result"
            #    detail = ['''The dataset has not been established yet, please
            #        go back and SELECT at least one dataset.''']
            #    self.error(heading=heading,detail=detail,error="No dataset Selected")
            #    return

            self.dataset.get_group()
            self.single_group = True
            #XZ, August 24,2010: Since self.single_group = True, it's safe to assign one species Id.
            self.species_id = webqtlDatabaseFunction.retrieveSpeciesId(self.cursor,
                                                                       self.dataset.group)

        #self.db_type = self.dataset.type
        if self.dataset.type == "Publish":
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
            self.header_fields = ['',
                                'ID',
                                'Description',
                                'Authors',
                                'Year',
                                'Max LRS',
                                'Max LRS Location']            

        elif self.dataset.type == "ProbeSet":
            self.search_fields = ['Name',
                                'Description',
                                'Probe_Target_Description',
                                'Symbol',
                                'Alias',
                                'GenbankId',
                                'UniGeneId',
                                'RefSeq_TranscriptId']
            self.header_fields = ['',
                                'ID',
                                'Symbol',
                                'Description',
                                'Location',
                                'Mean Expr',
                                'Max LRS',
                                'Max LRS Location']
        elif self.dataset.type == "Geno":
            self.search_fields = ['Name','Chr']
            self.header_fields = ['',
                                'ID',
                                'Location']

        self.search()
        self.gen_search_result()


    def gen_search_result(self):
        """Get the info displayed in the search result table from the set of results computed in
        the "search" function
        
        """
        self.trait_list = []
        # result_set represents the results for each search term; a search of 
        # "shh grin2b" would have two sets of results, one for each term
        print("self.results is:", pf(self.results))
        for result in self.results:
            if not result:
                continue

            seq = 1
            group = self.dataset.group

            species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=group)

            #### Excel file needs to be generated ####

            print("foo locals are:", locals())
            trait_id = result[0]
            this_trait = webqtlTrait(db=self.dataset, name=trait_id, cursor=self.cursor)
            this_trait.retrieveInfo(QTL=True)
            print("this_trait is:", pf(this_trait))
            self.trait_list.append(this_trait)

        if self.dataset.type == "ProbeSet":
            self.getTraitInfoForProbeSet(trait_list=self.trait_list, species=species)            
        elif self.dataset.type == "Publish":
            self.getTraitInfoForPublish(trait_list=self.trait_list, species=species)
        elif self.dataset.type == "Geno":
            self.getTraitInfoForGeno(trait_list=self.trait_list)


    def search(self):
        self.search_terms = parser.parse(self.fd['search_terms'])
        print("After parsing:", self.search_terms)

        self.results = []
        for a_search in self.search_terms:
            print("[kodak] item is:", pf(a_search))
            search_term = a_search['search_term']
            if a_search['key']:
                search_type = string.upper(a_search['key'])
            else:
                # We fall back to the dataset type as the key to get the right object
                search_type = self.dataset.type
                
            # This is throwing an error when a_search['key'] is None, so I changed above    
            #search_type = string.upper(a_search['key'])
            #if not search_type:
            #    # We fall back to the dataset type as the key to get the right object
            #    search_type = self.dataset.type

            search_ob = do_search.DoSearch.get_search(search_type)
            search_class = getattr(do_search, search_ob)
            self.results.extend(search_class(search_term,
                                    self.dataset,
                                    self.cursor,
                                    self.db_conn).run())
                
            print("in the search results are:", self.results)


    #ZS: This should be handled in the parser
    def encregexp(self,str):
        if not str:
            return []
        else:
            wildcardkeyword = str.strip()
            wildcardkeyword = string.replace(wildcardkeyword,',',' ')
            wildcardkeyword = string.replace(wildcardkeyword,';',' ')
            wildcardkeyword = wildcardkeyword.split()
        NNN = len(wildcardkeyword)
        for i in range(NNN):
            keyword = wildcardkeyword[i]
            keyword = string.replace(keyword,"*",".*")
            keyword = string.replace(keyword,"?",".")
            wildcardkeyword[i] = keyword#'[[:<:]]'+ keyword+'[[:>:]]'
        return wildcardkeyword
    

    def getTraitInfoForGeno(self, trait_list):

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


    def getTraitInfoForPublish(self, trait_list, species=''):

        for this_trait in trait_list:
            if not this_trait.haveinfo:
                this_trait.retrieveInfo(QTL=1)

            description = this_trait.post_publication_description
            if this_trait.confidential:
                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
                    description = this_trait.pre_publication_description
            this_trait.description_display = description

            try:
                this_trait.pubmed_text =  int(this_trait.year)
            except:
                this_trait.pubmed_text = "N/A"

            if this_trait.pubmed_id:
                this_trait.pubmed_link = webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id

            #LRS and its location
            this_trait.LRS_score_repr = 'N/A'
            this_trait.LRS_score_value = 0
            this_trait.LRS_location_repr = 'N/A'
            this_trait.LRS_location_value = 1000000

            if this_trait.lrs:
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


    def getTraitInfoForProbeSet(self, trait_list=None, species=''):

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

            # Save it for the jinja2 tablet
            this_trait.description_display = description_display

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
            """ % (self.db_conn.escape_string(str(this_trait.db.id)),
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
