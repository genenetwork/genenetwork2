"""module contains the code to do the 
precomputations of sample data between
two entire datasets"""

import json
from typing import List
from base import data_set

from gn3.computations.correlations import fast_compute_all_sample_correlation
from gn3.computations.correlations import map_shared_keys_to_values

def get_dataset_dict_data(dataset_obj):
    """function to get the dataset data mapped to key"""
    dataset_obj.get_trait_data()
    return map_shared_keys_to_values(dataset_obj.samplelist,
                                     dataset_obj.trait_data)


def fetch_datasets(base_dataset_name: str, target_dataset_name: str) ->List:
    """query to fetch create datasets and fetch traits
    all traits of a dataset"""

    # doesnt work for temp

    base_dataset = data_set.create_dataset(dataset_name=base_dataset_name)

    target_dataset = data_set.create_dataset(dataset_name=target_dataset_name)
    # replace with map

    return (map(get_dataset_dict_data,
                [base_dataset, target_dataset]))


# in the base dataset we just need the traits
def pre_compute_sample_correlation(base_dataset: List,
                                   target_dataset: List) -> List:
    """function compute the correlation between the
    a whole dataset against a target
    input: target&base_dataset(contains traits and sample results)
    output: list containing the computed results

    precaution:function is expensive;targets only Exon and
    """

    for trait_info in base_dataset:

        yield fast_compute_all_sample_correlation(corr_method="pearson",
                                                  this_trait=trait_info,
                                                  target_dataset=target_dataset)


def cache_to_file(base_dataset_name: str, target_dataset_name: str):
    """function to cache the results to file"""

    # validate the datasets expiry first

    base_dataset_data, target_dataset_data = [list(dataset) for dataset in list(
        fetch_datasets(base_dataset_name, target_dataset_name))]


    try:
        with open("unique_file_name.json", "w") as file_handler:
        file_handler.write()

        dataset_correlation_results = list(pre_compute_sample_correlation(
            base_dataset_data, target_dataset_data))

        print(dataset_correlation_results)

        json.dump(dataset_correlation_results, file_handler)
    except Exception as error:
        raise error
