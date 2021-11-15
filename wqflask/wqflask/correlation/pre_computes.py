import json
import os
import hashlib

from base.data_set import query_table_timestamp
from base.webqtlConfig import TMPDIR
from json.decoder import JSONDecodeError
from redis import Redis

r = Redis()


def generate_filename(base_dataset_name, target_dataset_name, base_timestamp, target_dataset_timestamp):
    """generate unique filename"""

    string_unicode = f"{base_dataset_name}{target_dataset_name}{base_timestamp}{target_dataset_timestamp}sample_corr_compute".encode()
    return hashlib.md5(string_unicode).hexdigest()


def cache_compute_results(base_dataset_type,
                          base_dataset_name,
                          target_dataset_name,
                          corr_method,
                          correlation_results,
                          trait_name):
    # pass
    """function to cache correlation results for heavy computations"""

    # init assumption only caching probeset type
    # fix redis;issue potential redis_cache!=current_timestamp

    base_timestamp = query_table_timestamp(base_dataset_type)

    r.set(f"{base_dataset_type}timestamp", base_timestamp)

    target_dataset_timestamp = base_timestamp

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

    file_path = os.path.join(TMPDIR, f"{file_name}.json")

    try:
        with open(file_path, "r+") as json_file_handler:
            data = json.load(json_file_handler)

            data[trait_name] = correlation_results

            json_file_handler.seek(0)

            json.dump(data, json_file_handler)

            json_file_handler.truncate()

    except FileNotFoundError:
        with open(file_path, "w+") as file_handler:
            data = {}
            data[trait_name] = correlation_results

            json.dump(data, file_handler)

    # create the file only if it does not exists

    # else open the file to cache the results


def fetch_precompute_results(base_dataset_name, target_dataset_name, dataset_type, trait_name):
    """function to check for precomputed  results"""

    # check for redis timestamp

    # fix rely on the fact correlation run oftenly probeset is set

    base_timestamp = target_dataset_timestamp = r.get(f"{dataset_type}timestamp")
    if base_timestamp is None:
        return

    else:
        base_timestamp = target_dataset_timestamp = base_timestamp.decode(
            "utf-8")

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

    file_path = os.path.join(TMPDIR, f"{file_name}.json")

    results = None

    try:
        with open(file_path, "r+") as json_handler:
            correlation_results = json.load(json_handler)
            # print(correlation_results)

        return correlation_results.get(trait_name)

    except FileNotFoundError:
        pass


def pre_compute_dataset_vs_dataset(base_dataset, target_dataset, corr_method):
    """compute sample correlation between dataset vs dataset
    wn:heavy function should be invoked less frequently
    input:datasets_data(two dicts),corr_method

    output:correlation results for entire dataset against entire dataset
    """
    dataset_correlation_results = {}

    target_traits_data, base_traits_data = get_datasets_data(
        base_dataset, target_dataset_data)

    for (primary_trait_name, strain_values) in base_traits_data:

        this_trait_data = {
            "trait_sample_data": strain_values,
            "trait_id": primary_trait_name
        }

        trait_correlation_result = fast_compute_all_sample_correlation(
            corr_method=corr_method, this_trait=this_trait_data, target_dataset=target_traits_data)

        dataset_correlation_results[primary_trait_name] = trait_correlation_result

    return dataset_correlation_results


def get_datasets_data(base_dataset, target_dataset_data):
    """required to pass data in a given format to the pre compute
    function

    output:two dicts for datasets with key==trait and value==strains
    """
    target_traits_data = target_dataset.get_trait_data(
        base_dataset.group.all_samples_ordered())

    base_traits_data = base_dataset.get_trait_data(
        base_dataset.group.all_samples_ordered())

    samples_fetched = base_dataset.group.all_samples_ordered()

    target_results = map_shared_keys_to_values(
        samples_fetched, target_traits_data)
    base_results = map_shared_keys_to_values(
        samples_fetched, base_traits_data)

    return (target_results, base_results)
