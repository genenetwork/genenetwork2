
import os
import hashlib

from base.data_set import query_table_timestamp
from base.webqtlConfig import TMPDIR


def generate_filename(**kwargs):
    """generate unique filename"""

    base_dataset_name = kwargs["base_dataset"]
    target_dataset_name = kwargs["target_dataset"]
    base_timestamp = kwargs["base_timestamp"]
    target_dataset_timestamp = kwargs["target_timestamp"]

    string_unicode = f"{base_dataset_name}{target_dataset_name}{base_timestamp}{target_dataset_timestamp}sample_corr_compute".encode()
    hashlib.md5(string_unicode).hexdigest()


def cache_compute_results(start_vars,
    base_dataset_type,
    correlation_results,
    trait_name):
    # pass

    # init assumption only caching probeset type
    # fix redis;issue potential redis_cache!=current_timestamp
    base_timestamp = r.get(f"{base_dataset_type}timestamp")

    if base_timestamp is None:
        # fetch the timestamp
        base_timestamp = target_dataset_timestamp = query_table_timestamp(
            dataset_type)

        r.set(f"{dataset_type}timestamp", target_dataset_timestamp)

    file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

    file_path = os.path.join(TMPDIR, f"{file_name}.json")

       try:

            with open(file_path, "r+") as json_handler:

                results = json.load(json_handler)

                if results.get(trait_name) is not None:
                    results.update({trait_name: correlation_results})

                json.dump(results, json_handler)

        except FileNotFoundError:
            with open(file_path, "w") as json_handler:
                json.dump({trait_name: correlation_results}, json_handler)

def fetch_precompute_results(base_dataset_name,target_dataset_name,trait_name):
    """function to check for precomputed  results"""

    # check for redis timestamp

    # fix rely on the fact correlation run oftenly probeset is set

    base_timestamp = target_dataset_timestamp =  r.get(dataset_type)


    if base_timestamp is None:
        return

    else:
        file_name = generate_filename(
        base_dataset_name, target_dataset_name,
        base_timestamp, target_dataset_timestamp)

        try:
            with open(file_path,"r") as json_handler:
                correlation_results = json.load(json_handler)

                return correlation_results.get(trait_name)

        except FileNotFoundError:
            pass







