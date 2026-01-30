import uuid
from math import *
import requests
import unicodedata
from urllib.parse import urlencode, urljoin
import re

import json

from pymonad.maybe import Just, Maybe
from pymonad.tools import curry
from gn_libs.mysqldb import database_connection

from flask import g

from gn3.monads import MonadicDict

from gn2.base.data_set import create_dataset
from gn2.base.webqtlConfig import PUBMEDLINK_URL
from gn2.wqflask import parser
from gn2.wqflask import do_search

from gn2.utility.hmac import hmac_creation
from gn2.utility.tools import get_setting, GN3_LOCAL_URL, GN_GUILE_SERVER_URL
from gn2.utility.type_checking import is_str

MAX_SEARCH_RESULTS = 50000 # Max number of search results, passed to Xapian search (this needs to match the value in GN3!)


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
        self.search_type = "sql" # Assume it's an SQL search by default, since all searches will work with SQL

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

            if self.search_type == "xapian":
                # These four lines are borrowed from gsearch.py; probably need to put them somewhere else to avoid duplicated code
                chr_mb = curry(2, lambda chromosome, mb: f"Chr{chromosome}: {mb:.6f}")
                format3f = lambda x: f"{x:.3f}"
                convert_lod = lambda x: x / 4.61

                trait = MonadicDict(result)
                trait["index"] = Just(index)
                trait["display_name"] = trait["name"]
                trait["location"] = (Maybe.apply(chr_mb)
                                        .to_arguments(trait.pop("chr"), trait.pop("mb")))
                trait["lod_score"] = trait.pop("lrs").map(convert_lod).map(format3f)
                trait["additive"] = trait["additive"].map(format3f)
                trait["mean"] = trait["mean"].map(format3f)
                trait["lrs_location"] = (Maybe.apply(chr_mb)
                                        .to_arguments(trait.pop("geno_chr"), trait.pop("geno_mb")))

                description_text = trait['description'].maybe("N/A", lambda a: a)
                trait['description'] = Just(description_text)

                if self.dataset.type == "ProbeSet":
                    key = f"{trait.data['name']}:{trait.data['dataset']}"
                    trait["hmac"] = Just(f"{key}:{hmac_creation(key)}")
                elif self.dataset.type == "Publish":
                    inbredsetcode = trait.pop("inbredsetcode")
                    if inbredsetcode.map(len) == Just(3):
                        trait["display_name"] = (Maybe.apply(
                            curry(2, lambda inbredsetcode, name: f"{inbredsetcode}_{name}"))
                                                .to_arguments(inbredsetcode, trait["name"]))

                    key = f"{trait.data['name']}:{trait.data['dataset']}"
                    trait["hmac"] = Just(f"{key}:{hmac_creation(key)}")
                    authors_list = trait.pop("authors")
                    trait["authors"] = authors_list.map(lambda authors: ", ".join(authors))
                    trait["authors_display"] = authors_list.map(lambda authors: ", ".join(authors[:2] + ["et al."] if len(authors) >=2 else authors))
                    trait["pubmed_text"] = trait.get("year", Just("N/A")).map(str)
                    trait["pubmed_link"] = trait.get("pubmed_id", Just("N/A")).map(lambda pid: PUBMEDLINK_URL % pid if pid != "N/A" else "N/A")
                    trait["n_samples"] = trait.get("nsamples", Just("N/A")).map(str)
                trait_list.append(trait.data)
            else:
                trait_dict = {}
                trait_dict['index'] = index + 1
                trait_dict['dataset'] = self.dataset.name
                if self.dataset.type == "ProbeSet":
                    trait_dict['display_name'] = result['ProbeSet_Name']
                    trait_dict['hmac'] = f"{trait_dict['display_name']}:{trait_dict['dataset']}:{hmac_creation('{}:{}'.format(trait_dict['display_name'], trait_dict['dataset']))}"
                    trait_dict['symbol'] = "N/A" if result['Symbol'] is None else result['Symbol'].strip()
                    description_text = ""
                    if result['description'] is not None and str(result['description']) != "":
                        description_text = unicodedata.normalize("NFKD", result['description'].decode('latin1'))

                    target_string = result['Probe_Target_Description'].decode('utf-8') if result['Probe_Target_Description'] else ""
                    description_display = description_text if target_string is None or str(target_string) == "" else description_text + "; " + str(target_string).strip()
                    trait_dict['description'] = description_display

                    trait_dict['location'] = "N/A"
                    if (result['Chr'] is not None) and (result['Chr'] != "") and (result['Chr'] != "Un") and (result['Mb'] is not None) and (result['Mb'] != 0):
                        trait_dict['location'] = f"Chr{result['Chr']}: {float(result['Mb']):.6f}"

                    trait_dict['mean'] = "N/A" if result['Mean'] is None or result['Mean'] == "" else f"{result['Mean']:.3f}"
                    trait_dict['additive'] = "N/A" if result['additive'] is None or result['additive'] == "" else f"{result['additive']:.3f}"
                    trait_dict['lod_score'] = "N/A" if result['LRS'] is None or result['LRS'] == "" else f"{float(result['LRS']) / 4.61:.1f}"
                    trait_dict['lrs_location'] = "N/A" if result['geno_chr'] is None or result['geno_chr'] == "" or result['geno_mb'] is None else f"Chr{result['geno_chr']}: {float(result['geno_mb']):.6f}"
                elif self.dataset.type == "Geno":
                    trait_dict['display_name'] = str(result['Name'])
                    trait_dict['hmac'] = f"{trait_dict['display_name']}:{trait_dict['dataset']}:{hmac_creation('{}:{}'.format(trait_dict['display_name'], trait_dict['dataset']))}"
                    trait_dict['location'] = "N/A"
                    if (result['Geno_Chr'] is not None and result['Geno_Chr'] != "" and result['Geno_Chr'] != "NULL") and (result['Geno_Mb'] is not None and result['Geno_Mb'] != 0):
                        trait_dict['location'] = f"Chr{result['Geno_Chr']}: {float(result['Geno_Mb']):.6f}"
                elif self.dataset.type == "Publish":
                    # Check permissions on a trait-by-trait basis for phenotype traits
                    trait_dict['display_name'] = trait_dict['name'] = result['Id']
                    inbredsetcode = result['InbredSetCode']
                    if inbredsetcode and len(inbredsetcode) == 3:
                        trait_dict['display_name'] = f"{inbredsetcode}_{trait_dict['display_name']}"
                    key = f"{trait_dict['name']}:{trait_dict['dataset']}"
                    trait_dict['hmac'] = f"{key}:{hmac_creation(key)}"

                    trait_dict['description'] = result['Pre_publication_description'].decode('latin1') if result['Pre_publication_description'] else ""
                    if result['PubMed_ID'] and result['PubMed_ID'] != "NULL":
                        trait_dict['description'] = result['Post_publication_description'].decode('latin1') if result['Post_publication_description'] else ""

                    authors = result['Authors']
                    if authors:
                        authors_list = authors.split(',')
                        trait_dict['authors'] = authors
                        trait_dict['authors_display'] = ", ".join(authors_list[:2] + ["et al."] if len(authors_list) >= 2 else authors_list)
                    else:
                        trait_dict['authors'] = trait_dict['authors_display'] = ""

                    trait_dict['pubmed_text'] = str(result['Year']) if result['Year'] else ""

                    if result['PubMed_ID'] and result['PubMed_ID'] != "NULL":
                        trait_dict['pubmed_id'] = result['PubMed_ID']
                        trait_dict['pubmed_link'] = PUBMEDLINK_URL % result['PubMed_ID']
                    else:
                        trait_dict['pubmed_id'] = "N/A"
                        trait_dict['pubmed_link'] = "N/A"

                    trait_dict['mean'] = "N/A" if result['mean'] is None or result['mean'] == "" else f"{result['mean']:.3f}"
                    trait_dict['lod_score'] = "N/A" if result['LRS'] is None or result['LRS'] == "" else f"{float(result['LRS']) / 4.61:.1f}"
                    trait_dict['additive'] = "N/A" if result['additive'] is None or result['additive'] == "" else f"{result['additive']:.3f}"
                    trait_dict['lrs_location'] = "N/A" if result['Chr'] is None or result['Chr'] == "" or result['Mb'] is None else f"Chr{result['Chr']}: {float(result['Mb']):.6f}"
                    trait_dict['n_samples'] = "N/A" if result['NSamples'] is None or result['NSamples'] == "" else str(result['NSamples'])

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
                    elif key == "symbol":
                        self.max_widths[key] = len(trait[key])
                        if len(trait[key]) > 20:
                            self.max_widths[key] = 20
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

        # Set of terms compatible with Xapian currently (None is a search without a term)
        xapian_terms = ["POSITION", "MEAN", "LRS", "LOD", "RIF", "WIKI"]

        if all([(the_term['key'] in xapian_terms) or (not the_term['key'] and self.dataset.type != "Publish") for the_term in self.search_terms]):
            self.search_type = "xapian"
            self.results = requests.get(generate_xapian_request(self.dataset, self.search_terms, self.and_or)).json()
            if not len(self.results) or 'error' in self.results:
                self.results = []
                self.sql_search()
        else:
            self.sql_search()

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

    def sql_search(self):
        self.search_type = "sql"
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
            self.results.extend([dict(zip(the_search.field_names, row)) for row in results])

        if self.search_term_exists:
            if the_search != None:
                self.header_fields = the_search.header_fields


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
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
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
        urljoin(GN_GUILE_SERVER_URL, f"gene/aliases/{symbol_string}"))
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

def generate_xapian_request(dataset, search_terms, and_or):
    """ Generate the resquest to GN3 which queries Xapian """
    match dataset.type:
        case "ProbeSet":
            search_type = "gene"
        case "Publish":
            search_type = "phenotype"
        case "Geno":
            search_type = "genotype"
        case _: # This should never happen
            raise ValueError(f"Dataset types should only be ProbeSet, Publish, or Geno, not '{dataset.type}'")

    xapian_terms = f" {and_or.upper()} ".join([create_xapian_term(dataset, term) for term in search_terms])

    return urljoin(GN3_LOCAL_URL, "/api/search?" + urlencode({"query": xapian_terms,
                                                              "type": search_type,
                                                              "per_page": MAX_SEARCH_RESULTS}))

def create_xapian_term(dataset, term):
    """ Create Xapian term for each search term """
    search_term = term['search_term']
    xapian_term = f"dataset:{dataset.name.lower()} AND "
    match term['key']:
        case 'MEAN':
            return xapian_term + f"mean:{search_term[0]}..{search_term[1]}"
        case 'POSITION':
            return xapian_term + f"chr:{search_term[0].lower().replace('chr', '')} AND position:{int(search_term[1])*10**6}..{int(search_term[2])*10**6}"
        case 'AUTHOR':
            return xapian_term + f"author:{search_term[0]}"
        case 'RIF':
            return xapian_term + f"rif:{search_term[0]}"
        case 'WIKI':
            return xapian_term + f"wiki:{search_term[0]}"
        case 'LRS':
            xapian_term += f"peak:{search_term[0]}..{search_term[1]}"
            if len(search_term) == 5:
                xapian_term += f" AND peakchr:{search_term[2].lower().replace('chr', '')} AND peakmb:{float(search_term[3])}..{float(search_term[4])}"
            return xapian_term
        case 'LOD': # Basically just LRS search but all values are multiplied by 4.61
            xapian_term += f"peak:{float(search_term[0]) * 4.61}..{float(search_term[1]) * 4.61}"
            if len(search_term) == 5:
                xapian_term += f" AND peakchr:{search_term[2].lower().replace('chr', '')}"
                xapian_term += f" AND peakmb:{float(search_term[3])}..{float(search_term[4])}"
            return xapian_term
        case None:
            return xapian_term + f"{search_term[0]}"
