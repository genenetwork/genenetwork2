import re
import uuid
from math import *
import time
import re
import requests
from types import SimpleNamespace

from pprint import pformat as pf

import json

from base.data_set import create_dataset
from base.trait import create_trait
from base.webqtlConfig import PUBMEDLINK_URL
from wqflask import parser
from wqflask import do_search
from db import webqtlDatabaseFunction

from flask import Flask, g

from utility import hmac, helper_functions
from utility.authentication_tools import check_resource_availability
from utility.tools import GN2_BASE_URL
from utility.type_checking import is_str

from utility.logger import getLogger
logger = getLogger(__name__ )

from utility.benchmark import Bench

class SearchResultPage(object):
    #maxReturn = 3000

    def __init__(self, kw):
        """
            This class gets invoked after hitting submit on the main menu (in
            views.py).
        """

        ###########################################
        #   Names and IDs of group / F2 set
        ###########################################

        self.uc_id = uuid.uuid4()
        self.go_term = None

        if kw['search_terms_or']:
            self.and_or = "or"
            self.search_terms = kw['search_terms_or']
        else:
            self.and_or = "and"
            self.search_terms = kw['search_terms_and']
        search = self.search_terms
        self.original_search_string = self.search_terms
        # check for dodgy search terms
        rx = re.compile(r'.*\W(href|http|sql|select|update)\W.*', re.IGNORECASE)
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

        #ZS: I don't like using try/except, but it seems like the easiest way to account for all possible bad searches here
        try:
            with Bench("Doing Query"):
                self.search()
        except:
           self.search_term_exists = False

        self.too_many_results = False
        if self.search_term_exists:
            if len(self.results) > 50000:
                self.trait_list = []
                self.too_many_results = True
            else:
                self.gen_search_result()

    def gen_search_result(self):
        """
        Get the info displayed in the search result table from the set of results computed in
        the "search" function

        """
        trait_list = []
        json_trait_list = []

        # result_set represents the results for each search term; a search of
        # "shh grin2b" would have two sets of results, one for each term

        if self.dataset.type == "ProbeSet":
            self.header_data_names = ['index', 'display_name', 'symbol', 'description', 'location', 'mean', 'lrs_score', 'lrs_location', 'additive']
        elif self.dataset.type == "Publish":
            self.header_data_names = ['index', 'display_name', 'description', 'mean', 'authors', 'pubmed_text', 'lrs_score', 'lrs_location', 'additive']
        elif self.dataset.type == "Geno":
            self.header_data_names = ['index', 'display_name', 'location']

        for index, result in enumerate(self.results):
            if not result:
                continue

            trait_dict = {}
            trait_dict['index'] = index + 1
            trait_dict['name'] = result[0]

            #ZS: Check permissions on a trait-by-trait basis for phenotype traits
            if self.dataset.type == "Publish":
                permissions = check_resource_availability(self.dataset, trait_dict['name'])
                if "view" not in permissions['data']:
                    continue

            trait_dict['display_name'] = result[0]
            if self.dataset.type == "Publish":
                if self.dataset.group_code:
                    trait_dict['display_name'] = self.dataset.group_code + "_" + result[0]

            trait_dict['dataset'] = self.dataset.name
            trait_dict['hmac'] = hmac.data_hmac('{}:{}'.format(trait_dict['name'], trait_dict['dataset']))
            if self.dataset.type == "ProbeSet":
                trait_dict['symbol'] = "N/A"
                if result[10]:
                    trait_dict['symbol'] = result[10]
                trait_dict['description'] = "N/A"
                description_string = result[2]
                if str(description_string) != "" and description_string != None:
                    description_display = description_string
                else:
                    description_display = trait_dict['symbol']

                target_string = result[3]
                if str(target_string) != "" and target_string != None:
                    description_display = description_display + "; " + target_string.strip()
                trait_dict['description'] = description_display

                trait_dict['location'] = "N/A"
                if (result[8] != "NULL" and result[8] != "") and (result[9] != 0):
                    trait_dict['location'] = f"Chr{result[8]}: {float(result[9]):.6f}"
                trait_dict['mean'] = "N/A"
                trait_dict['additive'] = "N/A"
                if result[4] != "" and result[4] != None:
                    trait_dict['mean'] = f"{result[4]:.3f}"
                try:
                    trait_dict['lod_score'] = f"{float(result[5]) / 4.61:.1f}"
                except:
                    trait_dict['lod_score'] = "N/A"
                try:
                    trait_dict['lrs_location'] = f"Chr{result[12]}: {float(result[13]):.6f}"
                except:
                    trait_dict['lrs_location'] = "N/A"
                if result[5] != "":
                    trait_dict['additive'] = f"{result[7]:.3f}"
            elif self.dataset.type == "Geno":
                trait_dict['location'] = "N/A"
                if (result[4] != "NULL" and result[4] != "") and (result[5] != 0):
                    trait_dict['location'] = f"Chr{result[4]}: {float(result[5]):.6f}"
            elif self.dataset.type == "Publish":
                trait_dict['description'] = "N/A"
                trait_dict['pubmed_id'] = "N/A"
                trait_dict['pubmed_link'] = "N/A"
                trait_dict['pubmed_text'] = "N/A"
                trait_dict['mean'] = "N/A"
                trait_dict['additive'] = "N/A"
                pre_pub_description = result[2].strip()
                post_pub_description = result[3].strip()
                if result[1] != "NULL" and result[1] != None:
                    trait_dict['pubmed_id'] = result[1]
                    trait_dict['pubmed_link'] = PUBMEDLINK_URL % trait_dict['pubmed_id']
                    trait_dict['description'] = post_pub_description
                else:
                    trait_dict['description'] = pre_pub_description

                if result[6].isdigit():
                    trait_dict['pubmed_text'] = result[6]

                trait_dict['authors'] = result[5]

                if result[4] != "" and result[4] != None:
                    trait_dict['mean'] = f"{result[4]:.3f}"

                try:
                    trait_dict['lod_score'] = f"{float(result[5]) / 4.61:.1f}"
                except:
                    trait_dict['lod_score'] = "N/A"

                try:
                    trait_dict['lrs_location'] = f"Chr{result[9]}: {float(result[10]):.6f}"
                except:
                    trait_dict['lrs_location'] = "N/A"

                if result[5] != "":
                    trait_dict['additive'] = f"{result[6]:.3f}"

            # Convert any bytes in dict to a normal utf-8 string
            for key in trait_dict.keys():
                if isinstance(trait_dict[key], bytes):
                    trait_dict[key] = trait_dict[key].decode('utf-8')
            trait_list.append(trait_dict)

        self.trait_list = trait_list

    def search(self):
        """
        This function sets up the actual search query in the form of a SQL statement and executes

        """
        self.search_terms = parser.parse(self.search_terms)

        combined_from_clause = ""
        combined_where_clause = ""
        previous_from_clauses = [] #The same table can't be referenced twice in the from clause

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
        search_term = a_search['search_term']
        search_operator = a_search['separator']
        search_type = {}
        search_type['dataset_type'] = self.dataset.type
        if a_search['key']:
            search_type['key'] = a_search['key'].upper()
        else:
            search_type['key'] = None

        search_ob = do_search.DoSearch.get_search(search_type)
        if search_ob:
            search_class = getattr(do_search, search_ob)
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
    for i in range(0, len(string), every):
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
    response = requests.get(GN2_BASE_URL + "/gn3/gene/aliases2/" + symbols_string)
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

