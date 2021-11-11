import json
import os
import hashlib

from base.data_set import query_table_timestamp
from base.webqtlConfig import TMPDIR
from redis import Redis

r = Redis()


def generate_filename(base_dataset_name, target_dataset_name, base_timestamp, target_dataset_timestamp):
    """generate unique filename"""

    string_unicode = f"{base_dataset_name}{target_dataset_name}{base_timestamp}{target_dataset_timestamp}sample_corr_compute".encode()
    return hashlib.md5(string_unicode).hexdigest()


def cache_compute_results(base_dataset_type,
                          base_dataset_name,
                          target_dataset_name,
                          correlation_results,
                          trait_name):
    # pass
    """function to cache correlation results for heavy computations"""

    # init assumption only caching probeset type
    # fix redis;issue potential redis_cache!=current_timestamp
    base_timestamp = r.get(f"{base_dataset_type}timestamp")

    if base_timestamp is None:
        # fetch the timestamp
        base_timestamp = query_table_timestamp(
            base_dataset_type)
        r.set(f"{base_dataset_type}timestamp", base_timestamp)

    target_dataset_timestamp = base_timestamp

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

    file_path = os.path.join(TMPDIR, f"{file_name}.json")

    try:

        with open(file_path, "r+") as json_handler:

            results = json.load(json_handler)
            results[trait_name] = correlation_results

            json.dump(results, json_handler)

    except FileNotFoundError:

        with open(file_path, "w+") as write_json_handler:
            json.dump({trait_name: correlation_results}, write_json_handler)


def fetch_precompute_results(base_dataset_name, target_dataset_name, dataset_type, trait_name):
    """function to check for precomputed  results"""

    # check for redis timestamp

    # fix rely on the fact correlation run oftenly probeset is set

    base_timestamp = target_dataset_timestamp = r.get(f"{dataset_type}timestamp")

    if base_timestamp is None:
        return

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

    file_path = os.path.join(TMPDIR, f"{file_name}.json")

    try:
        with open(file_path, "r") as json_handler:
            correlation_results = json.load(json_handler)
            return correlation_results.get(trait_name)

    except FileNotFoundError:
        pass
