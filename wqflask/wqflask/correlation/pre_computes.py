import json
import os
import hashlib
from pathlib import Path
from flask import g
from utility.tools import GN_PROXY_URL

from base.data_set import query_table_timestamp
from base.webqtlConfig import TMPDIR

from gn3.authentication import get_highest_user_access_role


def fetch_all_cached_metadata(dataset_name):
    """in a gvein dataset fetch all the traits metadata"""
    file_name = generate_filename(dataset_name, suffix="metadata")

    file_path = os.path.join(TMPDIR, file_name)

    try:
        with open(file_path, "r+") as file_handler:
            dataset_metadata = json.load(file_handler)
            return (file_path, dataset_metadata)

    except FileNotFoundError:
        Path(file_path).touch(exist_ok=True)
        return (file_path, {})


def cache_new_traits_metadata(dataset_metadata: dict, new_traits_metadata, file_path: str):
    """function to cache the new traits metadata"""

    if bool(new_traits_metadata):
        dataset_metadata.update(new_traits_metadata)

    with open(file_path, "w+") as file_handler:
        json.dump(dataset_metadata, file_handler)


def generate_filename(*args, suffix="", file_ext="json"):
    """given a list of args generate a unique filename"""

    string_unicode = f"{*args,}".encode()
    return f"{hashlib.md5(string_unicode).hexdigest()}_{suffix}.{file_ext}"


def cache_compute_results(base_dataset_type,
                          base_dataset_name,
                          target_dataset_name,
                          corr_method,
                          correlation_results,
                          trait_name):
    """function to cache correlation results for heavy computations"""

    base_timestamp = query_table_timestamp(base_dataset_type)

    target_dataset_timestamp = base_timestamp

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp,
        suffix="corr_precomputes")

    file_path = os.path.join(TMPDIR, file_name)

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


def fetch_precompute_results(base_dataset_name,
                             target_dataset_name,
                             dataset_type,
                             trait_name):
    """function to check for precomputed  results"""

    base_timestamp = target_dataset_timestamp = query_table_timestamp(
        dataset_type)
    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp,
        suffix="corr_precomputes")

    file_path = os.path.join(TMPDIR, file_name)

    try:
        with open(file_path, "r+") as json_handler:
            correlation_results = json.load(json_handler)

        return correlation_results.get(trait_name)

    except FileNotFoundError:
        pass


def pre_compute_dataset_vs_dataset(base_dataset,
                                   target_dataset,
                                   corr_method):
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

        trait_correlation_result = compute_all_sample_correlation(
            corr_method=corr_method,
            this_trait=this_trait_data,
            target_dataset=target_traits_data)

        dataset_correlation_results[primary_trait_name] = trait_correlation_result

    return dataset_correlation_results


def get_datasets_data(base_dataset, target_dataset_data):
    """required to pass data in a given format to the pre compute
    function

    (works for bxd only probeset datasets)

    output:two dicts for datasets with key==trait and value==strains
    """
    samples_fetched = base_dataset.group.all_samples_ordered()
    target_traits_data = target_dataset.get_trait_data(
        samples_fetched)

    base_traits_data = base_dataset.get_trait_data(
        samples_fetched)

    target_results = map_shared_keys_to_values(
        samples_fetched, target_traits_data)
    base_results = map_shared_keys_to_values(
        samples_fetched, base_traits_data)

    return (target_results, base_results)


def get_file_size(file_path):
    """params:file_path
       return:size of file in MB
"""
    file = Path(file_path)
    size_in_bytes = file.stat().st_size
    return float(size_in_bytes)/(1024**2)


def consume_json_file_handler(file_path, prefix=""):
    """function to read any json file stream
    or load based on size assumption:one object"""

    with open(file_path) as file_handler:
        if get_file_size(file_path) > 50:

            streamed_json = [obj for obj in ijson.items(
                file_handler, prefix, use_float=True)]
            return streamed_json if prefix != "" else streamed_json[0]

        return json.load(file_handler)


def generate_button_configs(dev_mode="DEBUG"):
    user_id = ((g.user_session.record.get(b"user_id") or b"").decode("utf-8"))

    try:
        user_role = get_highest_user_access_role(
            user_id=user_id, resource_id="", gn_proxy_url=GN_PROXY_URL)["admin"]

    except Exception:
        user_role = False

    return True if (user_role or dev_mode == "DEBUG") else False
