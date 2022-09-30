import csv
import json
import os
import hashlib
from pathlib import Path

from base.data_set import query_table_timestamp
from base.webqtlConfig import TEXTDIR
from base.webqtlConfig import TMPDIR

from json.decoder import JSONDecodeError


def fetch_all_cached_metadata(dataset_name):
    """in a gvein dataset fetch all the traits metadata"""
    file_name = generate_filename(dataset_name, suffix="metadata")

    file_path = Path(TMPDIR, file_name)

    try:
        with open(file_path, "r+") as file_handler:
            dataset_metadata = json.load(file_handler)

            return (file_path, dataset_metadata)

    except FileNotFoundError:
        pass

    except JSONDecodeError:
        file_path.unlink()

    file_path.touch(exist_ok=True)

    return (file_path, {})


def cache_new_traits_metadata(dataset_metadata: dict, new_traits_metadata, file_path: str):
    """function to cache the new traits metadata"""

    if (dataset_metadata == {} and new_traits_metadata == {}):
        return

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


def fetch_text_file(dataset_name, conn, text_dir=TMPDIR):
    """fetch textfiles with strain vals if exists"""

    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (dataset_name,))
        results = cursor.fetchone()
    if results:
        try:
            for file in os.listdir(text_dir):
                if file.startswith(f"ProbeSetFreezeId_{results[0]}_"):
                    return os.path.join(text_dir, file)
        except FileNotFoundError:
            pass


def read_text_file(sample_dict, file_path):

    def __fetch_id_positions__(all_ids, target_ids):
        _vals = []
        _posit = [0]  # alternative for parsing

        for (idx, strain) in enumerate(all_ids, 1):
            if strain in target_ids:
                _vals.append(target_ids[strain])
                _posit.append(idx)

        return (_posit, _vals)

    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        _posit, sample_vals = __fetch_id_positions__(
            next(csv_reader)[1:], sample_dict)
        return (sample_vals, [",".join([line[i] for i in _posit]) for line in csv_reader])


def write_db_to_textfile(db_name, conn, text_dir=TMPDIR):

    def __generate_file_name__(db_name):
        # todo add expiry time and checker
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (db_name,))
            results = cursor.fetchone()
            if (results):
                return f"ProbeSetFreezeId_{results[0]}_{results[1]}"

    def __parse_to_dict__(results):
        ids = ["ID"]
        data = {}
        for (trait, strain, val) in results:
            if strain not in ids:
                ids.append(strain)
            if trait in data:
                data[trait].append(val)
            else:
                data[trait] = [trait, val]
        return (data, ids)

    def __write_to_file__(file_path, data, col_names):
        with open(file_path, 'w+', encoding='UTF8') as file_handler:

            writer = csv.writer(file_handler)
            writer.writerow(col_names)
            writer.writerows(data.values())
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT ProbeSet.Name, Strain.Name, ProbeSetData.value "
            "FROM Strain LEFT JOIN ProbeSetData "
            "ON Strain.Id = ProbeSetData.StrainId "
            "LEFT JOIN ProbeSetXRef ON ProbeSetData.Id = ProbeSetXRef.DataId "
            "LEFT JOIN ProbeSet ON ProbeSetXRef.ProbeSetId = ProbeSet.Id "
            "WHERE ProbeSetXRef.ProbeSetFreezeId IN "
            "(SELECT Id FROM ProbeSetFreeze WHERE Name = %s) "
            "ORDER BY Strain.Name",
            (db_name,))
        results = cursor.fetchall()
        file_name = __generate_file_name__(
            db_name)
        if (results and file_name):
            __write_to_file__(os.path.join(text_dir, file_name),
                              *__parse_to_dict__(results))
