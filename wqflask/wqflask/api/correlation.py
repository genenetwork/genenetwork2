from __future__ import absolute_import, division, print_function

import collections

import scipy

from MySQLdb import escape_string as escape

from flask import g

from base import data_set
from base.trait import create_trait, retrieve_sample_data

from wqflask.correlation.show_corr_results import generate_corr_json
from wqflask.correlation import correlation_functions

from utility import webqtlUtil, helper_functions, corr_result_helpers
from utility.benchmark import Bench

import utility.logger
logger = utility.logger.getLogger(__name__ )

def do_correlation(start_vars):
    assert('db' in start_vars)
    assert('target_db' in start_vars)
    assert('trait_id' in start_vars)

    this_dataset = data_set.create_dataset(dataset_name = start_vars['db'])
    target_dataset = data_set.create_dataset(dataset_name = start_vars['target_db'])
    this_trait = create_trait(dataset = this_dataset, name = start_vars['trait_id'])
    this_trait = retrieve_sample_data(this_trait, this_dataset)

    corr_params = init_corr_params(start_vars)

    corr_results = calculate_results(this_trait, this_dataset, target_dataset, corr_params)
    #corr_results = collections.OrderedDict(sorted(corr_results.items(), key=lambda t: -abs(t[1][0])))

    final_results = []
    for _trait_counter, trait in enumerate(list(corr_results.keys())[:corr_params['return_count']]):
        if corr_params['type'] == "tissue":
            [sample_r, num_overlap, sample_p, symbol] = corr_results[trait]
            result_dict = {
                "trait"     : trait,
                "sample_r"  : sample_r,
                "#_strains" : num_overlap,
                "p_value"   : sample_p,
                "symbol"    : symbol
            }
        elif corr_params['type'] == "literature" or corr_params['type'] == "lit":
            [gene_id, sample_r] = corr_results[trait]
            result_dict = {
                "trait"     : trait,
                "sample_r"  : sample_r,
                "gene_id"   : gene_id
            }
        else:
            [sample_r, sample_p, num_overlap] = corr_results[trait]
            result_dict = {
                "trait"     : trait,
                "sample_r"  : sample_r,
                "#_strains" : num_overlap,
                "p_value"   : sample_p
            }

        final_results.append(result_dict)

    # json_corr_results = generate_corr_json(final_corr_results, this_trait, this_dataset, target_dataset, for_api = True)

    return final_results

def calculate_results(this_trait, this_dataset, target_dataset, corr_params):
    corr_results = {}

    target_dataset.get_trait_data()

    if corr_params['type'] == "tissue":
        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        corr_results = do_tissue_correlation_for_all_traits(this_trait, trait_symbol_dict, corr_params)
        sorted_results = collections.OrderedDict(sorted(list(corr_results.items()),
                                                        key=lambda t: -abs(t[1][1])))
    elif corr_params['type'] == "literature" or corr_params['type'] == "lit": #ZS: Just so a user can use either "lit" or "literature"
        trait_geneid_dict = this_dataset.retrieve_genes("GeneId")
        corr_results = do_literature_correlation_for_all_traits(this_trait, this_dataset, trait_geneid_dict, corr_params)
        sorted_results = collections.OrderedDict(sorted(list(corr_results.items()),
                                                 key=lambda t: -abs(t[1][1])))
    else:
        for target_trait, target_vals in list(target_dataset.trait_data.items()):
            result = get_sample_r_and_p_values(this_trait, this_dataset, target_vals, target_dataset, corr_params['type'])
            if result is not None:
                corr_results[target_trait] = result

        sorted_results = collections.OrderedDict(sorted(list(corr_results.items()), key=lambda t: -abs(t[1][0])))

    return sorted_results

def do_tissue_correlation_for_all_traits(this_trait, trait_symbol_dict, corr_params, tissue_dataset_id=1):
    #Gets tissue expression values for the primary trait
    primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(symbol_list = [this_trait.symbol])

    if this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
        primary_trait_tissue_values = primary_trait_tissue_vals_dict[this_trait.symbol.lower()]

        corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(symbol_list=list(trait_symbol_dict.values()))

        tissue_corr_data = {}
        for trait, symbol in list(trait_symbol_dict.items()):
            if symbol and symbol.lower() in corr_result_tissue_vals_dict:
                this_trait_tissue_values = corr_result_tissue_vals_dict[symbol.lower()]

                result = correlation_functions.cal_zero_order_corr_for_tiss(primary_trait_tissue_values,
                                                                            this_trait_tissue_values,
                                                                            corr_params['method'])

                tissue_corr_data[trait] = [result[0], result[1], result[2], symbol]

        return tissue_corr_data

def do_literature_correlation_for_all_traits(this_trait, target_dataset, trait_geneid_dict, corr_params):
    input_trait_mouse_gene_id = convert_to_mouse_gene_id(target_dataset.group.species.lower(), this_trait.geneid)

    lit_corr_data = {}
    for trait, gene_id in list(trait_geneid_dict.items()):
        mouse_gene_id = convert_to_mouse_gene_id(target_dataset.group.species.lower(), gene_id)

        if mouse_gene_id and str(mouse_gene_id).find(";") == -1:
            result = g.db.execute(
                """SELECT value
                    FROM LCorrRamin3
                    WHERE GeneId1='%s' and
                            GeneId2='%s'
                """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
            ).fetchone()
            if not result:
                result = g.db.execute("""SELECT value
                    FROM LCorrRamin3
                    WHERE GeneId2='%s' and
                            GeneId1='%s'
                """ % (escape(mouse_gene_id), escape(input_trait_mouse_gene_id))
                ).fetchone()
            if result:
                lit_corr = result.value
                lit_corr_data[trait] = [gene_id, lit_corr]
            else:
                lit_corr_data[trait] = [gene_id, 0]
        else:
            lit_corr_data[trait] = [gene_id, 0]

    return lit_corr_data

def get_sample_r_and_p_values(this_trait, this_dataset, target_vals, target_dataset, type):
    """
    Calculates the sample r (or rho) and p-value

    Given a primary trait and a target trait's sample values,
    calculates either the pearson r or spearman rho and the p-value
    using the corresponding scipy functions.
    """

    this_trait_vals = []
    shared_target_vals = []
    for i, sample in enumerate(target_dataset.group.samplelist):
        if sample in this_trait.data:
            this_sample_value = this_trait.data[sample].value
            target_sample_value = target_vals[i]
            this_trait_vals.append(this_sample_value)
            shared_target_vals.append(target_sample_value)

    this_trait_vals, shared_target_vals, num_overlap = corr_result_helpers.normalize_values(this_trait_vals, shared_target_vals)

    if type == 'pearson':
        sample_r, sample_p = scipy.stats.pearsonr(this_trait_vals, shared_target_vals)
    else:
        sample_r, sample_p = scipy.stats.spearmanr(this_trait_vals, shared_target_vals)

    if num_overlap > 5:
        if scipy.isnan(sample_r):
            return None
        else:
            return [sample_r, sample_p, num_overlap]

def convert_to_mouse_gene_id(species=None, gene_id=None):
    """If the species is rat or human, translate the gene_id to the mouse geneid

    If there is no input gene_id or there's no corresponding mouse gene_id, return None

    """
    if not gene_id:
        return None

    mouse_gene_id = None

    if species == 'mouse':
        mouse_gene_id = gene_id

    elif species == 'rat':

        query = """SELECT mouse
                FROM GeneIDXRef
                WHERE rat='%s'""" % escape(gene_id)

        result = g.db.execute(query).fetchone()
        if result != None:
            mouse_gene_id = result.mouse

    elif species == 'human':

        query = """SELECT mouse
                FROM GeneIDXRef
                WHERE human='%s'""" % escape(gene_id)

        result = g.db.execute(query).fetchone()
        if result != None:
            mouse_gene_id = result.mouse

    return mouse_gene_id

def init_corr_params(start_vars):
    method = "pearson"
    if 'method' in start_vars:
        method = start_vars['method']

    type = "sample"
    if 'type' in start_vars:
        type = start_vars['type']

    return_count = 500
    if 'return_count' in start_vars:
        assert(start_vars['return_count'].isdigit())
        return_count = int(start_vars['return_count'])

    corr_params = {
        'method'       : method,
        'type'         : type,
        'return_count' : return_count
    }

    return corr_params