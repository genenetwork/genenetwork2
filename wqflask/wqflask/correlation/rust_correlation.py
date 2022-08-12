"""module contains integration code for rust-gn3"""
import json
from functools import reduce
from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_gn3_api import create_target_this_trait
from wqflask.correlation.correlation_gn3_api import lit_for_trait_list
from wqflask.correlation.correlation_gn3_api import do_lit_correlation
from gn3.computations.correlations import compute_all_lit_correlation
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data
from gn3.db_utils import database_connector


def compute_top_n_lit(corr_results, this_dataset, this_trait) -> dict:
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    geneid_dict = {trait_name: geneid for (trait_name, geneid) in geneid_dict.items() if
                   corr_results.get(trait_name)}
    with database_connector() as conn:
        return reduce(
            lambda acc, corr: {**acc, **corr},
            compute_all_lit_correlation(
                conn=conn, trait_lists=list(geneid_dict.items()),
                species=species, gene_id=this_trait_geneid),
            {})

    return {}


def compute_top_n_tissue(this_dataset, this_trait, traits, method):

    # refactor lots of rpt

    trait_symbol_dict = dict({
        trait_name: symbol
        for (trait_name, symbol)
        in this_dataset.retrieve_genes("Symbol").items()
        if traits.get(trait_name)})

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


def merge_results(dict_a: dict, dict_b: dict, dict_c: dict) -> list[dict]:
    """code to merge diff corr  into individual dicts
    a"""

    def __merge__(trait_name, trait_corrs):
        return {
            trait_name: {
                **trait_corrs,
                **dict_b.get(trait_name, {}),
                **dict_c.get(trait_name, {})
            }
        }
    return [__merge__(tname, tcorrs) for tname, tcorrs in dict_a.items()]

def __compute_sample_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the sample correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    all_samples = json.loads(start_vars["sample_vals"])
    sample_data = get_sample_corr_data(
        sample_type=start_vars["corr_samples_group"], all_samples=all_samples,
        dataset_samples=this_dataset.group.all_samples_ordered())
    target_dataset.get_trait_data(list(sample_data.keys()))

    target_data = []
    for (key, val) in target_dataset.trait_data.items():
        lts = [key] + [str(x) for x in val]
        r = ",".join(lts)
        target_data.append(r)


    return run_correlation(
        target_data, list(sample_data.values()), method, ",", corr_type,
        n_top)

def __compute_tissue_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the tissue correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
    corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
        symbol_list=list(trait_symbol_dict.values()))

    data = parse_tissue_corr_data(
        symbol_name=this_trait.symbol,
        symbol_dict=get_trait_symbol_and_tissue_values(
            symbol_list=[this_trait.symbol]),
        dataset_symbols=trait_symbol_dict,
        dataset_vals=corr_result_tissue_vals_dict)

    if data:
        return run_correlation(data[1], data[0], method, ",", "tissue")
    return {}

def __compute_lit_corr__(
        start_vars: dict, corr_type: str, method: str, n_top: int,
        target_trait_info: tuple):
    """Compute the literature correlations"""
    (this_dataset, this_trait, target_dataset, sample_data) = target_trait_info
    target_dataset_type = target_dataset.type
    this_dataset_type = this_dataset.type
    (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
        this_trait, this_dataset)

    with database_connector() as conn:
        return compute_all_lit_correlation(
            conn=conn, trait_lists=list(geneid_dict.items()),
            species=species, gene_id=this_trait_geneid)
    return {}

def compute_correlation_rust(
        start_vars: dict, corr_type: str, method: str = "pearson",
        n_top: int = 500, compute_all: bool = False):
    """function to compute correlation"""
    target_trait_info = create_target_this_trait(start_vars)
    (this_dataset, this_trait, target_dataset, sample_data) = (
        target_trait_info)

    ## Replace this with `match ...` once we hit Python 3.10
    corr_type_fns = {
        "sample": __compute_sample_corr__,
        "tissue": __compute_tissue_corr__,
        "lit": __compute_lit_corr__
    }
    results = corr_type_fns[corr_type](
        start_vars, corr_type, method, n_top, target_trait_info)
    ## END: Replace this with `match ...` once we hit Python 3.10

    top_tissue_results = {}
    top_lit_results = {}
    if compute_all:
        # example compute of compute both correlation
        top_tissue_results = compute_top_n_tissue(
            this_dataset,this_trait,results,method)
        top_lit_results = compute_top_n_lit(results,this_dataset,this_trait)

    return {
        "correlation_results": merge_results(
            results, top_tissue_results, top_lit_results),
        "this_trait": this_trait.name,
        "target_dataset": start_vars['corr_dataset'],
        "return_results": n_top
    }
