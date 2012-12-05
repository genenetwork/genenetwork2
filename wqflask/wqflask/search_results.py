from __future__ import absolute_import, division, print_function

from wqflask import app

from flask import render_template

###################################################
#                                                 #
# This file uses only spaces for indentation      #
#                                                 #
###################################################

#import string
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
from base.data_set import create_dataset
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from wqflask import parser
from wqflask import do_search
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction

from utility import formatting

#from base.JinjaPage import JinjaEnv, JinjaPage


class SearchResultPage(templatePage):
    #maxReturn = 3000


    def __init__(self, fd):
        print("initing SearchResultPage")
        #import logging_tree
        #logging_tree.printout()
        self.fd = fd
        templatePage.__init__(self, fd)
        assert self.openMysql(), "Couldn't open MySQL"

        print("fd is:", pf(fd))
        print("fd.dict is:", pf(fd['dataset']))
        self.dataset = fd['dataset']

        # change back to self.dataset
        #if not self.dataset or self.dataset == 'spacer':
        #    #Error, No dataset selected
        #    heading = "Search Result"
        #    detail = ['''No dataset was selected for this search, please
        #        go back and SELECT at least one dataset.''']
        #    self.error(heading=heading,detail=detail,error="No dataset Selected")
        #    return

        ###########################################
        #   Names and IDs of group / F2 set
        ###########################################
        
        # All Phenotypes is a special case we'll deal with later
        if self.dataset == "All Phenotypes":
            self.cursor.execute("""
                select PublishFreeze.Name, InbredSet.Name, InbredSet.Id from PublishFreeze,
                InbredSet where PublishFreeze.Name not like 'BXD300%' and InbredSet.Id =
                PublishFreeze.InbredSetId""")
            results = self.cursor.fetchall()
            self.dataset = map(lambda x: DataSet(x[0], self.cursor), results)
            self.dataset_groups = map(lambda x: x[1], results)
            self.dataset_group_ids = map(lambda x: x[2], results)
        else:
            print("self.dataset is:", pf(self.dataset))
            # Replaces a string with an object
            self.dataset = create_dataset(self.dataset)
            print("self.dataset is now:", pf(self.dataset))
 
        self.search()
        self.gen_search_result()


    def gen_search_result(self):
        """
        Get the info displayed in the search result table from the set of results computed in
        the "search" function

        """
        self.trait_list = []
        
        group = self.dataset.group
        species = webqtlDatabaseFunction.retrieve_species(group=group)        
        
        # result_set represents the results for each search term; a search of 
        # "shh grin2b" would have two sets of results, one for each term
        print("self.results is:", pf(self.results))
        for result in self.results:
            if not result:
                continue
            
            #### Excel file needs to be generated ####

            print("foo locals are:", locals())
            trait_id = result[0]
            this_trait = webqtlTrait(dataset=self.dataset, name=trait_id)
            this_trait.retrieve_info(QTL=True)
            self.trait_list.append(this_trait)

        self.dataset.get_trait_info(self.trait_list, species)    


    def search(self):
        self.search_terms = parser.parse(self.fd['search_terms'])
        print("After parsing:", self.search_terms)

        self.results = []
        for a_search in self.search_terms:
            print("[kodak] item is:", pf(a_search))
            search_term = a_search['search_term']
            search_operator = a_search['separator']
            if a_search['key']:
                search_type = a_search['key'].upper()
            else:
                # We fall back to the dataset type as the key to get the right object
                search_type = self.dataset.type
                
            print("search_type is:", pf(search_type))

            # This is throwing an error when a_search['key'] is None, so I changed above    
            #search_type = string.upper(a_search['key'])
            #if not search_type:
            #    search_type = self.dataset.type

            search_ob = do_search.DoSearch.get_search(search_type)
            search_class = getattr(do_search, search_ob)
            the_search = search_class(search_term,
                                    search_operator,
                                    self.dataset,
                                    )
            self.results.extend(the_search.run())
            print("in the search results are:", self.results)

        self.header_fields = the_search.header_fields


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
