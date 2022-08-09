"""module contains integration code for rust-gn3"""
import json
from wqflask.correlation.correlation_functions import get_trait_symbol_and_tissue_values
from wqflask.correlation.correlation_gn3_api import create_target_this_trait
from gn3.computations.rust_correlation import run_correlation
from gn3.computations.rust_correlation import get_sample_corr_data
from gn3.computations.rust_correlation import parse_tissue_corr_data


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

        results = run_correlation(
            target_data, list(sample_data.values()), method, ",")


    if corr_type == "tissue":

        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        corr_result_tissue_vals_dict = get_trait_symbol_and_tissue_values(
            symbol_list=list(trait_symbol_dict.values()))

        data = parse_tissue_corr_data(symbol_name=this_trait.symbol,
                                      symbol_dict=get_trait_symbol_and_tissue_values(
                                          symbol_list=[this_trait.symbol]),
                                      dataset_symbols=trait_symbol_dict,
                                      dataset_vals=corr_result_tissue_vals_dict)

        if data:
            results = run_correlation(
                data[1], data[0], method, ",")

    return {"correlation_results": results[0:n_top],
            "this_trait": this_trait.name,
            "target_dataset": start_vars['corr_dataset'],
            "return_results": n_top
            }
