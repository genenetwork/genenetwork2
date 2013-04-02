from __future__ import absolute_import, print_function, division

from wqflask import app

from flask import render_template

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

from flask import Flask, g

# Instead of importing HT we're going to build a class below until we can eliminate it
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.data_set import create_dataset
from base.trait import GeneralTrait
from wqflask import parser
from wqflask import do_search
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction

from utility import formatting

#from base.JinjaPage import JinjaEnv, JinjaPage


class SearchResultPage():
    #maxReturn = 3000


    def __init__(self, kw):

        ###########################################
        #   Names and IDs of group / F2 set
        ###########################################

        # All Phenotypes is a special case we'll deal with later
        #if kw['dataset'] == "All Phenotypes":
        #    self.cursor.execute("""
        #        select PublishFreeze.Name, InbredSet.Name, InbredSet.Id from PublishFreeze,
        #        InbredSet where PublishFreeze.Name not like 'BXD300%' and InbredSet.Id =
        #        PublishFreeze.InbredSetId""")
        #    results = self.cursor.fetchall()
        #    self.dataset = map(lambda x: DataSet(x[0], self.cursor), results)
        #    self.dataset_groups = map(lambda x: x[1], results)
        #    self.dataset_group_ids = map(lambda x: x[2], results)
        #else:

        self.results = []

        if 'q' in kw:
            #self.quick_search = True
            self.search_terms = kw['q']
            print("self.search_terms is: ", self.search_terms)
            self.quick_search()
        else:
            #self.quick_search = False
            self.search_terms = kw['search_terms']
            self.dataset = create_dataset(kw['dataset'])
            self.search()
        self.gen_search_result()


    def gen_search_result(self):
        """
        Get the info displayed in the search result table from the set of results computed in
        the "search" function

        """
        self.trait_list = []
        
        species = webqtlDatabaseFunction.retrieve_species(self.dataset.group.name)        
        
        # result_set represents the results for each search term; a search of 
        # "shh grin2b" would have two sets of results, one for each term
        print("self.results is:", pf(self.results))
        for result in self.results:
            if not result:
                continue
            
            #### Excel file needs to be generated ####

            print("foo locals are:", locals())
            trait_id = result[0]
            this_trait = GeneralTrait(dataset=self.dataset.name, name=trait_id)
            this_trait.retrieve_info(QTL=True)
            self.trait_list.append(this_trait)

        self.dataset.get_trait_info(self.trait_list, species)

    def quick_search(self):
        self.search_terms = parser.parse(self.search_terms)
        print("After parsing:", self.search_terms)

        search_types = ["quick_phenotype", "quick_mrna_assay"]

        for search_category in search_types:
            search_ob = do_search.DoSearch.get_search(search_category)
            search_class = getattr(do_search, search_ob)
            for a_search in self.search_terms:
                search_term = a_search['search_term']
                the_search = search_class(search_term)
                self.results.extend(the_search.run())
                print("in the search results are:", self.results)

        #for a_search in self.search_terms:
        #    search_term = a_search['search_term']
        #
        #    #Do mRNA assay search
        #    search_ob = do_search.DoSearch.get_search("quick_mrna_assay")
        #    search_class = getattr(do_search, search_ob)
        #    the_search = search_class(search_term)
        #    
        #    self.results.extend(the_search.run())
        #    print("in the search results are:", self.results)


        #return True

        #search_gene
        #search_geno
        #searhch_pheno
        #search_mrn
        #searhc_publish


    def search(self):
        self.search_terms = parser.parse(self.search_terms)
        print("After parsing:", self.search_terms)

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
            print("search_class is: ", pf(search_class))
            the_search = search_class(search_term,
                                    search_operator,
                                    self.dataset,
                                    )
            self.results.extend(the_search.run())
            print("in the search results are:", self.results)

        self.header_fields = the_search.header_fields
