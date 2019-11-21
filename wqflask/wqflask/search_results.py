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
import re
import requests

from pprint import pformat as pf

import json

from base.data_set import create_dataset
from base import trait
from wqflask import parser
from wqflask import do_search
from utility import webqtlUtil,tools
from db import webqtlDatabaseFunction

from wqflask import user_manager

from flask import render_template, Flask, g

from utility import formatting
from utility.type_checking import is_float, is_int, is_str, get_float, get_int, get_string

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

        self.uc_id = uuid.uuid4()
        self.go_term = None
        logger.debug("uc_id:", self.uc_id) # contains a unique id

        logger.debug("kw is:", kw)         # dict containing search terms
        if kw['search_terms_or']:
            self.and_or = "or"
            self.search_terms = kw['search_terms_or']
        else:
            self.and_or = "and"
            self.search_terms = kw['search_terms_and']
        search = self.search_terms
        # check for dodgy search terms
        rx = re.compile(r'.*\W(href|http|sql|select|update)\W.*',re.IGNORECASE)
        if rx.match(search):
            logger.info("Regex failed search")
            self.search_term_exists = False
            return
        else:
            self.search_term_exists = True

        self.results = []
        type = kw.get('type')
        if type == "Phenotypes":     # split datatype on type field
            dataset_type = "Publish"
        elif type == "Genotypes":
            dataset_type = "Geno"
        else:
            dataset_type = "ProbeSet"      # ProbeSet is default

        assert(is_str(kw.get('dataset')))
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
        trait_list = []
        json_trait_list = []

        species = webqtlDatabaseFunction.retrieve_species(self.dataset.group.name)
        # result_set represents the results for each search term; a search of
        # "shh grin2b" would have two sets of results, one for each term
        logger.debug("self.results is:", pf(self.results))

        for index, result in enumerate(self.results):
            if not result:
                continue

            #### Excel file needs to be generated ####

            trait_dict = {}
            trait_id = result[0]
            trait_dict['index'] = index + 1
            this_trait = trait.GeneralTrait(dataset=self.dataset, name=trait_id, get_qtl_info=True, get_sample_info=False)
            trait_dict['name'] = this_trait.name
            if this_trait.dataset.type == "Publish":
                trait_dict['display_name'] = this_trait.display_name
            else:
                trait_dict['display_name'] = this_trait.name
            trait_dict['dataset'] = this_trait.dataset.name
            trait_dict['hmac'] = user_manager.data_hmac('{}:{}'.format(this_trait.name, this_trait.dataset.name))
            if this_trait.dataset.type == "ProbeSet":
                trait_dict['symbol'] = this_trait.symbol
                trait_dict['description'] = this_trait.description_display.decode('utf-8', 'replace')
                trait_dict['location'] = this_trait.location_repr
                trait_dict['mean'] = "N/A"
                trait_dict['additive'] = "N/A"
                if this_trait.mean != "" and this_trait.mean != None:
                    trait_dict['mean'] = '%.3f' % this_trait.mean
                trait_dict['lrs_score'] = this_trait.LRS_score_repr
                trait_dict['lrs_location'] = this_trait.LRS_location_repr
                if this_trait.additive != "":
                    trait_dict['additive'] = '%.3f' % this_trait.additive
            elif this_trait.dataset.type == "Geno":
                trait_dict['location'] = this_trait.location_repr
            elif this_trait.dataset.type == "Publish":
                trait_dict['description'] = this_trait.description_display
                trait_dict['authors'] = this_trait.authors
                trait_dict['pubmed_id'] = "N/A"
                if this_trait.pubmed_id:
                    trait_dict['pubmed_id'] = this_trait.pubmed_id
                    trait_dict['pubmed_link'] = this_trait.pubmed_link
                trait_dict['pubmed_text'] = this_trait.pubmed_text
                trait_dict['lrs_score'] = this_trait.LRS_score_repr
                trait_dict['lrs_location'] = this_trait.LRS_location_repr
                trait_dict['additive'] = "N/A"
                if this_trait.additive != "":
                    trait_dict['additive'] = '%.3f' % this_trait.additive
            trait_list.append(trait_dict)
            #json_trait_list.append(trait.jsonable_table_row(this_trait, self.dataset.name, index + 1))

        self.trait_list = json.dumps(trait_list)
        #self.json_trait_list = json.dumps(json_trait_list)

    def search(self):
        """
        This function sets up the actual search query in the form of a SQL statement and executes

        """
        self.search_terms = parser.parse(self.search_terms)
        logger.debug("After parsing:", self.search_terms)

        combined_from_clause = ""
        combined_where_clause = ""
        previous_from_clauses = [] #The same table can't be referenced twice in the from clause

        logger.debug("len(search_terms)>1")
        symbol_list = []
        if self.dataset.type == "ProbeSet":
            for a_search in self.search_terms:
                if a_search['key'] == None:
                    symbol_list.append(a_search['search_term'][0])

            alias_terms = get_aliases(symbol_list, self.dataset.group.species)

            for i, a_search in enumerate(alias_terms):
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
                    where_clause = the_search.get_alias_where_clause()
                    combined_where_clause += "(" + where_clause + ")"
                    if self.and_or == "and":
                        combined_where_clause += "AND"
                    else:
                        combined_where_clause += "OR"

        for i, a_search in enumerate(self.search_terms):
            if a_search['key'] == "GO":
                self.go_term = a_search['search_term'][0]
                gene_list = get_GO_symbols(a_search)
                self.search_terms += gene_list
                continue
            else:
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
            results = the_search.execute(final_query)
            self.results.extend(results)

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
        else:
            search_type['key'] = None
        logger.debug("search_type is:", pf(search_type))

        search_ob = do_search.DoSearch.get_search(search_type)
        if search_ob:
            search_class = getattr(do_search, search_ob)
            logger.debug("search_class is: ", pf(search_class))
            the_search = search_class(search_term,
                                    search_operator,
                                    self.dataset,
                                    search_type['key']
                                    )
            return the_search
        else:
            return None

def get_GO_symbols(a_search):
    query = """SELECT genes
               FROM GORef
               WHERE goterm='{0}:{1}'""".format(a_search['key'], a_search['search_term'][0])

    gene_list = g.db.execute(query).fetchone()[0].strip().split()

    new_terms = []
    for gene in gene_list:
        this_term = dict(key=None,
                         separator=None,
                         search_term=[gene])

        new_terms.append(this_term)

    return new_terms

def insert_newlines(string, every=64):
    """ This is because it is seemingly impossible to change the width of the description column, so I'm just manually adding line breaks """
    lines = []
    for i in xrange(0, len(string), every):
        lines.append(string[i:i+every])
    return '\n'.join(lines)

def get_aliases(symbol_list, species):

    updated_symbols = []
    for symbol in symbol_list:
        if species == "mouse":
            updated_symbols.append(symbol.capitalize())
        elif species == "human":
            updated_symbols.append(symbol.upper())
        else:
            updated_symbols.append(symbol)

    symbols_string = ",".join(updated_symbols)

    filtered_aliases = []
    response = requests.get("http://gn2.genenetwork.org/gn3/gene/aliases2/" + symbols_string)
    if response:
        alias_lists = json.loads(response.content)
        seen = set()
        for aliases in alias_lists:
            for item in aliases[1]:
                if item in seen:
                    continue
                else:
                    filtered_aliases.append(item)
                    seen.add(item)

    search_terms = []
    for alias in filtered_aliases:
        the_search_term = {'key':         None,
                           'search_term': [alias],
                           'separator' :  None}
        search_terms.append(the_search_term)

    return search_terms

