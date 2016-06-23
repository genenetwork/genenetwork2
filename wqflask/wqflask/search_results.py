# from __future__ import absolute_import, print_function, division


import os
import cPickle
import re
import uuid
from math import *
import time
import math
import datetime
import collections

from pprint import pformat as pf

import json

from base.data_set import create_dataset
from base.trait import GeneralTrait
from wqflask import parser
from wqflask import do_search
from utility import webqtlUtil,tools
from db import webqtlDatabaseFunction

from flask import render_template

from utility import formatting

from utility.logger import getLogger
logger = getLogger(__name__ )

class SearchResultPage(object):
    #maxReturn = 3000

    def __init__(self, kw):
        """This class gets invoked after hitting submit on the main menu (in
views.py).

        """

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

        self.uc_id = uuid.uuid4()
        logger.debug("uc_id:", self.uc_id) # contains a unique id

        logger.debug("kw is:", kw)         # dict containing search terms
        if kw['search_terms_or']:
            self.and_or = "or"
            self.search_terms = kw['search_terms_or']
        else:
            self.and_or = "and"
            self.search_terms = kw['search_terms_and']
        self.search_term_exists = True
        self.results = []
        if kw['type'] == "Phenotypes":     # split datatype on type field
            dataset_type = "Publish"
        elif kw['type'] == "Genotypes":
            dataset_type = "Geno"
        else:
            dataset_type = "ProbeSet"      # ProbeSet is default
        self.dataset = create_dataset(kw['dataset'], dataset_type)
        logger.debug("search_terms:", self.search_terms)
        self.search()
        if self.search_term_exists:
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
        logger.debug("self.results is:", pf(self.results))
        for result in self.results:
            if not result:
                continue

            #### Excel file needs to be generated ####

            #logger.debug("foo locals are:", locals())
            trait_id = result[0]
            this_trait = GeneralTrait(dataset=self.dataset, name=trait_id, get_qtl_info=True, get_sample_info=False)
            self.trait_list.append(this_trait)

        self.dataset.get_trait_info(self.trait_list, species)

    #def get_group_species_tree(self):
    #    self.species_groups = collections.default_dict(list)
    #    for key in self.results:
    #        for item in self.results[key]:
    #            self.species_groups[item['result_fields']['species']].append(
    #                                        item['result_fields']['group_name'])

    def search(self):
        """This function sets up the actual search query in the form of a SQL
statement and executes

        """
        self.search_terms = parser.parse(self.search_terms)
        logger.debug("After parsing:", self.search_terms)

        if len(self.search_terms) > 1:
            logger.debug("len(search_terms)>1")
            combined_from_clause = ""
            combined_where_clause = ""
            previous_from_clauses = [] #The same table can't be referenced twice in the from clause
            for i, a_search in enumerate(self.search_terms):
                the_search = self.get_search_ob(a_search)
                if the_search != None:
                    get_from_clause = getattr(the_search, "get_from_clause", None)
                    if callable(get_from_clause):
                        from_clause = the_search.get_from_clause()
                        if from_clause in previous_from_clauses:
                            pass
                        else:
                            previous_from_clauses.append(from_clause)
                            combined_from_clause += from_clause
                    where_clause = the_search.get_where_clause()
                    combined_where_clause += "(" + where_clause + ")"
                    if (i+1) < len(self.search_terms):
                        if self.and_or == "and":
                            combined_where_clause += "AND"
                        else:
                            combined_where_clause += "OR"
                else:
                    self.search_term_exists = False
            if self.search_term_exists:
                combined_where_clause = "(" + combined_where_clause + ")"
                final_query = the_search.compile_final_query(combined_from_clause, combined_where_clause)
                logger.debug("final_query",final_query)
                results = the_search.execute(final_query)
                self.results.extend(results)
        else:
            logger.debug("len(search_terms)<=1")
            if self.search_terms == []:
                self.search_term_exists = False
            else:
                for a_search in self.search_terms:
                    the_search = self.get_search_ob(a_search)
                    if the_search != None:
                        self.results.extend(the_search.run())
                    else:
                        self.search_term_exists = False

        if self.search_term_exists:
            if the_search != None:
                self.header_fields = the_search.header_fields

    def get_search_ob(self, a_search):
        logger.debug("[kodak] item is:", pf(a_search))
        search_term = a_search['search_term']
        search_operator = a_search['separator']
        search_type = {}
        search_type['dataset_type'] = self.dataset.type
        if a_search['key']:
            search_type['key'] = a_search['key'].upper()
        logger.debug("search_type is:", pf(search_type))

        search_ob = do_search.DoSearch.get_search(search_type)
        if search_ob:
            search_class = getattr(do_search, search_ob)
            logger.debug("search_class is: ", pf(search_class))
            the_search = search_class(search_term,
                                    search_operator,
                                    self.dataset,
                                    )
            return the_search
        else:
            return None
