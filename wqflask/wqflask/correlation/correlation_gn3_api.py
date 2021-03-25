"""module that calls the gn3 api's to do the correlation """
import json
import requests
from wqflask.wqflask.correlation import correlation_functions

from wqflask.base import data_set
from wqflask.base.trait import create_trait
from wqflask.base.trait import retrieve_sample_data

GN3_CORRELATION_API = "http://127.0.0.1:8080/api/correlation"


def process_samples(start_vars, sample_names, excluded_samples=None):
    """process samples method"""
    sample_data = {}
    if not excluded_samples:
        excluded_samples = ()

        sample_vals_dict = json.loads(start_vars["sample_vals"])

        for sample in sample_names:
            if sample not in excluded_samples:
                val = sample_vals_dict[sample]
                if not val.strip().lower() == "x":
                    sample_data[str(sample)] = float(val)

    return sample_data


def create_target_this_trait(start_vars):
    """this function creates the required trait and target dataset for correlation"""

    this_dataset = data_set.create_dataset(dataset_name=start_vars['dataset'])
    target_dataset = data_set.create_dataset(
        dataset_name=start_vars['corr_dataset'])

    this_trait = create_trait(dataset=this_dataset,
                              name=start_vars['trait_id'])

    sample_data = process_samples(start_vars, this_dataset.group.samplelist)
    # target_dataset.get_trait_data(list(self.sample_data.keys()))

    this_trait = retrieve_sample_data(this_trait, this_dataset)

    target_dataset.get_trait_data(list(sample_data.keys()))

    return (this_dataset, this_trait, target_dataset, sample_data)


def compute_correlation(start_vars, method="pearson"):
    """compute correlation for to call gn3  api"""

    corr_type = start_vars['corr_type']

    (this_dataset, this_trait, target_dataset,
     sample_data) = create_target_this_trait(start_vars)

    # cor_results = compute_correlation(start_vars)

    method = start_vars['corr_sample_method']

    corr_input_data = {}

    if corr_type == "sample":
        corr_input_data = {
            "target_dataset": target_dataset.trait_data,
            "target_samplelist": target_dataset.samplelist,
            "trait_data": {
                "trait_sample_data": sample_data,
                "trait_id": start_vars["trait_id"]
            }
        }

        requests_url = f"{GN3_CORRELATION_API}/sample_x/{method}"

    elif corr_type == "tissue":
        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        primary_tissue_data, target_tissue_data = get_tissue_correlation_input(
            this_trait, trait_symbol_dict)

        corr_input_data = {
            "primary_tissue": primary_tissue_data,
            "target_tissues": target_tissue_data
        }

        requests_url = f"{GN3_CORRELATION_API}/tissue_corr/{method}"

    else:
        pass
        # lit correlation/literature
        # can fetch values in  gn3 not set up in gn3

    corr_results = requests.post(requests_url, json=corr_input_data)

    data = corr_results.json()

    return data


def get_tissue_correlation_input(this_trait, trait_symbol_dict):
    """Gets tissue expression values for the primary trait and target tissues values"""
    primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
        symbol_list=[this_trait.symbol])

    if this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
        primary_trait_tissue_values = primary_trait_tissue_vals_dict[this_trait.symbol.lower(
        )]

        corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list=list(trait_symbol_dict.values()))

        target_tissue_data = []
        for trait, symbol in list(trait_symbol_dict.items()):
            if symbol and symbol.lower() in corr_result_tissue_vals_dict:
                this_trait_tissue_values = corr_result_tissue_vals_dict[symbol.lower(
                )]

                this_trait_data = {"trait_id": trait,
                                   "tissue_values": this_trait_tissue_values}

                target_tissue_data.append(this_trait_data)

        primary_tissue_data = {
            "this_id": "TT",
            "tissue_values": primary_trait_tissue_values

        }

        return (primary_tissue_data, target_tissue_data)

    return None
