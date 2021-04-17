"""module that calls the gn3 api's to do the correlation """
import json
import requests
import time
from wqflask.correlation import correlation_functions

from base import data_set
from base.trait import create_trait
from base.trait import retrieve_sample_data
# gn3 lib
from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import benchmark_compute_all_sample
from gn3.computations.correlations import map_shared_keys_to_values
from gn3.computations.correlations import compute_all_tissue_correlation

GN3_CORRELATION_API = "http://127.0.0.1:8202/api/correlation"


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

    print("creating the dataset and trait")
    import time

    initial_time = time.time()

    this_dataset = data_set.create_dataset(dataset_name=start_vars['dataset'])
    target_dataset = data_set.create_dataset(
        dataset_name=start_vars['corr_dataset'])

    this_trait = create_trait(dataset=this_dataset,
                              name=start_vars['trait_id'])

    
    # target_dataset.get_trait_data(list(self.sample_data.keys()))

    # this_trait = retrieve_sample_data(this_trait, this_dataset)
    print(f"Starting to creat the target dataset ")
    dataset_start_time = time.time()
    sample_data = ()

    

    time_taken = time.time() - initial_time
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
        # corr_input_data = {
        #     "target_dataset": target_dataset.trait_data,
        #     "target_samplelist": target_dataset.samplelist,
        #     "trait_data": {
        #         "trait_sample_data": sample_data,
        #         "trait_id": start_vars["trait_id"]
        #     }
        # }

        sample_data = process_samples(start_vars, this_dataset.group.samplelist)
        target_dataset.get_trait_data(list(sample_data.keys()))
        this_trait = retrieve_sample_data(this_trait, this_dataset)



        this_trait_data = {
            "trait_sample_data": sample_data,
            "trait_id": start_vars["trait_id"]
        }

        initial_time = time.time()
        print("Calling sample correlation")
        results = map_shared_keys_to_values(
            target_dataset.samplelist, target_dataset.trait_data)
        correlation_results = compute_all_sample_correlation(corr_method=method,
                                                             this_trait=this_trait_data,
                                                             target_dataset=results)

        print("Time taken is>>>>",time.time()-initial_time)

        # requests_url = f"{GN3_CORRELATION_API}/sample_x/{method}"
        return correlation_results

    elif corr_type == "tissue":
        trait_symbol_dict = this_dataset.retrieve_genes("Symbol")
        time_to_retrieve = time.time()
        primary_tissue_data, target_tissue_data = get_tissue_correlation_input(
            this_trait, trait_symbol_dict)
        print("Time taken to retrieve this is",time.time()-time_to_retrieve)

        corr_input_data = {
            "primary_tissue": primary_tissue_data,
            "target_tissues_dict": target_tissue_data
        }
        print("Calling tissue correlation")
        initial_time = time.time()
        correlation_results = compute_all_tissue_correlation(primary_tissue_dict=corr_input_data["primary_tissue"],
                                                             target_tissues_data=corr_input_data["target_tissues_dict"],
                                                             corr_method=method)

        time_taken = time.time()
        print("Time taken is ??????",time_taken-initial_time)

        # requests_url = f"{GN3_CORRELATION_API}/tissue_corr/{method}"
        return correlation_results

    elif corr_type == "lit":
        (this_trait_geneid, geneid_dict, species) = do_lit_correlation(
            this_trait, this_dataset, target_dataset)

        requests_url = f"{GN3_CORRELATION_API}/lit_corr/{species}/{this_trait_geneid}"
        corr_input_data = geneid_dict

    print("Sending this request")
    corr_results = requests.post(requests_url, json=corr_input_data)

    data = corr_results.json()

    return data


def do_lit_correlation(this_trait, this_dataset, target_dataset):
    geneid_dict = this_dataset.retrieve_genes("GeneId")
    species = this_dataset.group.species.lower()

    this_trait_geneid = this_trait.geneid
    this_trait_gene_data = {
        this_trait.name: this_trait_geneid
    }

    return (this_trait_geneid, geneid_dict, species)


def get_tissue_correlation_input(this_trait, trait_symbol_dict):
    """Gets tissue expression values for the primary trait and target tissues values"""
    primary_trait_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
        symbol_list=[this_trait.symbol])

    if this_trait.symbol.lower() in primary_trait_tissue_vals_dict:
        primary_trait_tissue_values = primary_trait_tissue_vals_dict[this_trait.symbol.lower(
        )]

        corr_result_tissue_vals_dict = correlation_functions.get_trait_symbol_and_tissue_values(
            symbol_list=list(trait_symbol_dict.values()))
        primary_tissue_data = {
            "this_id": this_trait.name,
            "tissue_values": primary_trait_tissue_values

        }
        target_tissue_data = {
            "trait_symbol_dict": trait_symbol_dict,
            "symbol_tissue_vals_dict": corr_result_tissue_vals_dict
        }

        return (primary_tissue_data, target_tissue_data)

    return None
