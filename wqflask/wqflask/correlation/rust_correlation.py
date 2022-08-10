"""module contains integration code for rust-gn3"""
import json
from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_gn3_api import create_target_this_trait
from wqflask.correlation.correlation_gn3_api import lit_for_trait_list
from wqflask.correlation.correlation_gn3_api import do_lit_correlation
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data
from gn3.db_utils import database_connector


def compute_top_n_lit(corr_results, this_dataset, this_trait):
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    geneid_dict = {trait_name: geneid for (trait_name, geneid) in geneid_dict.items() if
                   corr_results.get(trait_name)}

    conn = database_connector()

    with conn:

        correlation_results = compute_all_lit_correlation(
            conn=conn, trait_lists=list(geneid_dict.items()),
            species=species, gene_id=this_trait_geneid)

    return correlation_results


def compute_top_n_tissue(this_dataset, this_trait, traits, method):

    # refactor lots of rpt

    trait_symbol_dict = dict({trait_name: symbol for (
        trait_name, symbol) in this_dataset.retrieve_genes("Symbol").items() if traits.get(trait_name)})

    corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
        symbol_list=list(trait_symbol_dict.values()))

    data = parse_tissue_corr_data(symbol_name=this_trait.symbol,
                                  symbol_dict=get_trait_symbol_and_tissue_values(
                                      symbol_list=[this_trait.symbol]),
                                  dataset_symbols=trait_symbol_dict,
                                  dataset_vals=corr_result_tissue_vals_dict)

    if data:
        return run_correlation(
            data[1], data[0], method, ",", "tissue")

    return {}


def merge_results(dict_a, dict_b, dict_c):
    """code to merge diff corr  into individual dicts
    a"""

    correlation_results = []

    for (key, val) in dict_a.items():

        if key in dict_b:

            dict_a[key].update(dict_b[key])

        if key in dict_c:

            dict_a[key].update(dict_c[key])

        correlation_results.append({key: dict_a[key]})

    return correlation_results


def compute_correlation_rust(start_vars: dict, corr_type: str,
                             method: str = "pearson", n_top: int = 500):
    """function to compute correlation"""

    (this_dataset, this_trait, target_dataset,
     sample_data) = create_target_this_trait(start_vars)

    if corr_type == "sample":

        all_samples = json.loads(start_vars["sample_vals"])
        sample_data = get_sample_corr_data(sample_type=start_vars["corr_samples_group"],
                                           all_samples=all_samples,
                                           dataset_samples=this_dataset.group.all_samples_ordered())

        target_dataset.get_trait_data(list(sample_data.keys()))

        target_data = []
        for (key, val) in target_dataset.trait_data.items():
            lts = [key] + [str(x) for x in val]
            r = ",".join(lts)
            target_data.append(r)


        results = run_correlation(target_data,
                                  list(sample_data.values()),
                                  method,
                                  ",",
                                  corr_type,
                                  n_top)

        # example compute of compute both correlation



        top_tissue_results = compute_top_n_tissue(this_dataset,this_trait,results,method)


        top_lit_results = compute_top_n_lit(results,this_dataset,this_trait)


        # merging the results

        results = merge_results(results,top_tissue_results,top_lit_results)

    if corr_type == "tissue":

        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
            symbol_list=list(trait_symbol_dict.values()))

        data = parse_tissue_corr_data(symbol_name=this_trait.symbol,
                                      symbol_dict=get_trait_symbol_and_tissue_values(
                                          symbol_list=[this_trait.symbol]
                                      ),
                                      dataset_symbols=trait_symbol_dict,
                                      dataset_vals=corr_result_tissue_vals_dict)

        if data:
            results = run_correlation(
                data[1], data[0], method, ",", "tissue")

    return {"correlation_results": results,
            "this_trait": this_trait.name,
            "target_dataset": start_vars['corr_dataset'],
            "return_results": n_top
            }
