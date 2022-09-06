import re
import uuid
from math import *
import time
import re
import requests
from types import SimpleNamespace
import unicodedata

from pprint import pformat as pf

import json

from base.data_set import create_dataset
from base.trait import create_trait
from base.webqtlConfig import PUBMEDLINK_URL
from wqflask import parser
from wqflask import do_search
from db import webqtlDatabaseFunction

from wqflask.database import database_connection

from utility import hmac, helper_functions
from utility.authentication_tools import check_resource_availability
from utility.tools import GN2_BASE_URL
from utility.type_checking import is_str


class SearchResultPage:
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
        rx = re.compile(
            r'.*\W(href|http|sql|select|update)\W.*', re.IGNORECASE)
        if rx.match(search):
            self.search_term_exists = False
            return
        else:
            self.search_term_exists = True

        self.results = []
        max_result_count = 100000 # max number of results to display
        type = kw.get('type')
        if type == "Phenotypes":     # split datatype on type field
            max_result_count = 50000
            dataset_type = "Publish"
        elif type == "Genotypes":
            dataset_type = "Geno"
        else:
            dataset_type = "ProbeSet"      # ProbeSet is default

        assert(is_str(kw.get('dataset')))
        self.dataset = create_dataset(kw['dataset'], dataset_type)

        # I don't like using try/except, but it seems like the easiest way to account for all possible bad searches here
        try:
            self.search()
        except:
            self.search_term_exists = False

        self.too_many_results = False
        if self.search_term_exists:
            if len(self.results) > max_result_count:
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

            trait_dict['dataset'] = self.dataset.name
            if self.dataset.type == "ProbeSet":
                trait_dict['display_name'] = result[2]
                trait_dict['hmac'] = hmac.data_hmac('{}:{}'.format(trait_dict['display_name'], trait_dict['dataset']))
                trait_dict['symbol'] = "N/A" if result[3] is None else result[3].strip()
                description_text = ""
                if result[4] is not None and str(result[4]) != "":
                    description_text = unicodedata.normalize("NFKD", result[4].decode('latin1'))

                target_string = result[5].decode('utf-8') if result[5] else ""
                description_display = description_text if target_string is None or str(target_string) == "" else description_text + "; " + str(target_string).strip()
                trait_dict['description'] = description_display

                trait_dict['location'] = "N/A"
                if (result[6] is not None) and (result[6] != "") and (result[6] != "Un") and (result[7] is not None) and (result[7] != 0):
                    trait_dict['location'] = f"Chr{result[6]}: {float(result[7]):.6f}"

                trait_dict['mean'] = "N/A" if result[8] is None or result[8] == "" else f"{result[8]:.3f}"
                trait_dict['additive'] = "N/A" if result[12] is None or result[12] == "" else f"{result[12]:.3f}"
                trait_dict['lod_score'] = "N/A" if result[9] is None or result[9] == "" else f"{float(result[9]) / 4.61:.1f}"
                trait_dict['lrs_location'] = "N/A" if result[13] is None or result[13] == "" or result[14] is None else f"Chr{result[13]}: {float(result[14]):.6f}"
            elif self.dataset.type == "Geno":
                trait_dict['display_name'] = str(result[0])
                trait_dict['hmac'] = hmac.data_hmac('{}:{}'.format(trait_dict['display_name'], trait_dict['dataset']))
                trait_dict['location'] = "N/A"
                if (result[4] != "NULL" and result[4] != "") and (result[5] != 0):
                    trait_dict['location'] = f"Chr{result[4]}: {float(result[5]):.6f}"
            elif self.dataset.type == "Publish":
                # Check permissions on a trait-by-trait basis for phenotype traits
                trait_dict['name'] = trait_dict['display_name'] = str(result[0])
                trait_dict['hmac'] = hmac.data_hmac('{}:{}'.format(trait_dict['name'], trait_dict['dataset']))
                permissions = check_resource_availability(self.dataset, trait_dict['display_name'])
                if not any(x in permissions['data'] for x in ["view", "edit"]):
                    continue

                if result[10]:
                    trait_dict['display_name'] = str(result[10]) + "_" + str(result[0])
                trait_dict['description'] = "N/A"
                trait_dict['pubmed_id'] = "N/A"
                trait_dict['pubmed_link'] = "N/A"
                trait_dict['pubmed_text'] = "N/A"
                trait_dict['mean'] = "N/A"
                trait_dict['additive'] = "N/A"
                pre_pub_description = "N/A" if result[1] is None else result[1].strip()
                post_pub_description = "N/A" if result[2] is None else result[2].strip()
                if result[5] != "NULL" and result[5] != None:
                    trait_dict['pubmed_id'] = result[5]
                    trait_dict['pubmed_link'] = PUBMEDLINK_URL % trait_dict['pubmed_id']
                    trait_dict['description'] = post_pub_description
                else:
                    trait_dict['description'] = pre_pub_description

                if result[4].isdigit():
                    trait_dict['pubmed_text'] = result[4]

                trait_dict['authors'] = result[3]
                trait_dict['authors_display'] = trait_dict['authors']
                author_list = trait_dict['authors'].split(",")
                if len(author_list) >= 2:
                    trait_dict['authors_display'] = (",").join(author_list[:2]) + ", et al."

                if result[6] != "" and result[6] != None:
                    trait_dict['mean'] = f"{result[6]:.3f}"

                try:
                    trait_dict['lod_score'] = f"{float(result[7]) / 4.61:.1f}"
                except:
                    trait_dict['lod_score'] = "N/A"

                try:
                    trait_dict['lrs_location'] = f"Chr{result[11]}: {float(result[12]):.6f}"
                except:
                    trait_dict['lrs_location'] = "N/A"

                trait_dict['additive'] = "N/A" if not result[8] else f"{result[8]:.3f}"

            trait_dict['trait_info_str'] = trait_info_str(trait_dict, self.dataset.type)

            # Convert any bytes in dict to a normal utf-8 string
            for key in trait_dict.keys():
                if isinstance(trait_dict[key], bytes):
                    try:
                        trait_dict[key] = trait_dict[key].decode('utf-8')
                    except UnicodeDecodeError:
                        trait_dict[key] = trait_dict[key].decode('latin-1')

            trait_list.append(trait_dict)

        if self.results:
            self.max_widths = {}
            for i, trait in enumerate(trait_list):
                for key in trait.keys():
                    if key == "authors":
                        authors_string = ",".join(str(trait[key]).split(",")[:2]) + ", et al."
                        self.max_widths[key] = max(len(authors_string), self.max_widths[key]) if key in self.max_widths else len(str(authors_string))
                    else:
                        self.max_widths[key] = max(len(str(trait[key])), self.max_widths[key]) if key in self.max_widths else len(str(trait[key]))

            self.wide_columns_exist = False
            if self.dataset.type == "Publish":
                if (self.max_widths['display_name'] > 25 or self.max_widths['description'] > 100 or self.max_widths['authors']> 80):
                    self.wide_columns_exist = True
            if self.dataset.type == "ProbeSet":
                if (self.max_widths['display_name'] > 25 or self.max_widths['symbol'] > 25 or self.max_widths['description'] > 100):
                    self.wide_columns_exist = True


        self.trait_list = trait_list

    def search(self):
        """
        This function sets up the actual search query in the form of a SQL statement and executes

        """
        self.search_terms = parser.parse(self.search_terms)

        combined_from_clause = ""
        combined_where_clause = ""
        # The same table can't be referenced twice in the from clause
        previous_from_clauses = []

        for i, a_search in enumerate(self.search_terms):
            if a_search['key'] == "GO":
                self.go_term = a_search['search_term'][0]
                gene_list = get_GO_symbols(a_search)
                self.search_terms += gene_list
                continue
            else:
                the_search = self.get_search_ob(a_search)
                if the_search != None:
                    if a_search['key'] == None and self.dataset.type == "ProbeSet":
                        alias_terms = get_alias_terms(a_search['search_term'][0], self.dataset.group.species)
                        alias_where_clauses = []
                        for alias_search in alias_terms:
                            alias_search_ob = self.get_search_ob(alias_search)
                            if alias_search_ob != None:
                                get_from_clause = getattr(
                                    alias_search_ob, "get_from_clause", None)
                                if callable(get_from_clause):
                                    from_clause = alias_search_ob.get_from_clause()
                                    if from_clause in previous_from_clauses:
                                        pass
                                    else:
                                        previous_from_clauses.append(from_clause)
                                        combined_from_clause += from_clause
                                where_clause = alias_search_ob.get_alias_where_clause()
                                alias_where_clauses.append(where_clause)

                        get_from_clause = getattr(
                            the_search, "get_from_clause", None)
                        if callable(get_from_clause):
                            from_clause = the_search.get_from_clause()
                            if from_clause in previous_from_clauses:
                                pass
                            else:
                                previous_from_clauses.append(from_clause)
                                combined_from_clause += from_clause

                        where_clause = the_search.get_where_clause()
                        alias_where_clauses.append(where_clause)

                        combined_where_clause += "(" + " OR ".join(alias_where_clauses) + ")"
                        if (i + 1) < len(self.search_terms):
                            if self.and_or == "and":
                                combined_where_clause += "AND"
                            else:
                                combined_where_clause += "OR"
                    else:
                        get_from_clause = getattr(
                            the_search, "get_from_clause", None)
                        if callable(get_from_clause):
                            from_clause = the_search.get_from_clause()
                            if from_clause in previous_from_clauses:
                                pass
                            else:
                                previous_from_clauses.append(from_clause)
                                combined_from_clause += from_clause

                        where_clause = the_search.get_where_clause()
                        combined_where_clause += "(" + where_clause + ")"
                        if (i + 1) < len(self.search_terms):
                            if self.and_or == "and":
                                combined_where_clause += "AND"
                            else:
                                combined_where_clause += "OR"
                else:
                    self.search_term_exists = False

        if self.search_term_exists:
            combined_where_clause = "(" + combined_where_clause + ")"
            final_query = the_search.compile_final_query(
                combined_from_clause, combined_where_clause)

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

def trait_info_str(trait, dataset_type):
    """Provide a string representation for given trait"""
    def __trait_desc(trt):
        if dataset_type == "Geno":
            return f"Marker: {trait['display_name']}"
        return trait['description'] or "N/A"

    def __symbol(trt):
        if dataset_type == "ProbeSet":
            return (trait['symbol'] or "N/A")[:20]

    def __lrs(trt):
        if dataset_type == "Geno":
            return 0
        else:
            if trait['lod_score'] != "N/A":
                return (
                    f"{float(trait['lod_score']):0.3f}" if float(trait['lod_score']) > 0
                    else f"{trait['lod_score']}")
            else:
                return "N/A"

    def __lrs_location(trt):
        if 'lrs_location' in trait:
            return trait['lrs_location']
        else:
            return "N/A"

    def __location(trt):
        if 'location' in trait:
            return trait['location']
        else:
            return None

    def __mean(trt):
        if 'mean' in trait:
            return trait['mean']
        else:
            return 0

    return "{}|||{}|||{}|||{}|||{}|||{}|||{}|||{}".format(
        trait['display_name'], trait['dataset'], __trait_desc(trait), __symbol(trait),
        __location(trait), __mean(trait), __lrs(trait), __lrs_location(trait))

def get_GO_symbols(a_search):
    gene_list = None
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT genes FROM GORef WHERE goterm=%s",
                       (f"{a_search['key']}:{a_search['search_term'][0]}",))
        gene_list = cursor.fetchone()[0].strip().split()

    new_terms = []
    for gene in gene_list:
        new_terms.append(dict(key=None, separator=None, search_term=[gene]))

    return new_terms


def insert_newlines(string, every=64):
    """ This is because it is seemingly impossible to change the width of the description column, so I'm just manually adding line breaks """
    lines = []
    for i in range(0, len(string), every):
        lines.append(string[i:i + every])
    return '\n'.join(lines)


def get_alias_terms(symbol, species):
    if species == "mouse":
        symbol_string = symbol.capitalize()
    elif species == "human":
        symbol_string = symbol.upper()
    else:
        return []

    filtered_aliases = []
    response = requests.get(
        GN2_BASE_URL + "/gn3/gene/aliases/" + symbol_string)
    if response:
        alias_list = json.loads(response.content)

        seen = set()
        for item in alias_list:
            if item in seen:
                continue
            else:
                filtered_aliases.append(item)
                seen.add(item)

    alias_terms = []
    for alias in filtered_aliases:
        the_search_term = {'key': None,
                           'search_term': [alias],
                           'separator': None}
        alias_terms.append(the_search_term)

    return alias_terms
