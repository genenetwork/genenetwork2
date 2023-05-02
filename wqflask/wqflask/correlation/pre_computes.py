import csv
import json
import os
import hashlib
import datetime

import lmdb
import pickle
from pathlib import Path
from gn3.db_utils import database_connection
from base.data_set import query_table_timestamp
from base.webqtlConfig import TEXTDIR
from base.webqtlConfig import TMPDIR

from utility.tools import SQL_URI

from json.decoder import JSONDecodeError

def cache_trait_metadata(dataset_name, data):


    try:
        with lmdb.open(os.path.join(TMPDIR,f"metadata_{dataset_name}"),map_size=20971520) as env:
            with  env.begin(write=True) as  txn:
                data_bytes = pickle.dumps(data)
                txn.put(f"{dataset_name}".encode(), data_bytes)
                current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                txn.put(b"creation_date", current_date.encode())
                return "success"
    except lmdb.Error as  error:
        pass

def read_trait_metadata(dataset_name,dataset_type):
    try:
        with lmdb.open(os.path.join("/tmp/",f"metadata_{dataset_type}"),            readonly=True, lock=False) as env:
            with env.begin() as txn:
                metadata =  txn.get(dataset_name.encode())
                return (pickle.loads(metadata)["data"] if metadata else {})
    except lmdb.Error as error:
        return {}



def parse_lmdb_dataset(strain_names,target_strains,data):
    _vals = [] 
    _posit = [0]
    def __fetch_id_positions__(all_ids, target_ids):
        _vals = []
        _posit = [0]  # alternative for parsing

        for (idx, strain) in enumerate(strain_names, 1):
            if strain in target_strains:
                _vals.append(target_strains[strain])
                _posit.append(idx)

        return (_posit, _vals)
    _posit,sample_vals = __fetch_id_positions__(strain_names,target_strains)
    return (sample_vals,[[line[i] for i in _posit] for line in data.values()])

def read_lmdb_strain_files(dataset_type,dataset_name,sql_uri=SQL_URI):
    # target file path for example probeset  and name used to generate the name

    def __sanitise_filename__(filename):
        ttable = str.maketrans({" ": "_", "/": "_", "\\": "_"})
        return str.translate(filename, ttable)



    def __generate_file_name__(db_name):     
        # todo add expiry time and checker

        with database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (db_name,))
                results = cursor.fetchone()
                if (results):
                    return __sanitise_filename__(
                        f"ProbeSetFreezeId_{results[0]}_{results[1]}")
    """

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
        return (sample_vals, [[line[i] for i in _posit] for line in csv_reader])


    """


    try:
        with lmdb.open(os.path.join("/tmp","Probesets"),readonly=True,lock=False) as env:
            with env.begin() as txn:
                filename = __generate_file_name__ (dataset_name)
                if filename:
                    data = txn.get(filename.encode())
  

                    col_ids = pickle.loads(data)["data"]

                    data = pickle.loads(data)["strain_names"]

                    return (col_ids,data)

                    # parse 
               
                return {}

    except Exception as error:
        breakpoint()
        return {}

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




def fetch_text_file(dataset_name, conn, text_dir=TMPDIR):
    """fetch textfiles with strain vals if exists"""

    def __file_scanner__(text_dir, target_file):
        for file in os.listdir(text_dir):
            if file.startswith(f"ProbeSetFreezeId_{target_file}_"):
                return os.path.join(text_dir, file)

    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (dataset_name,))
        results = cursor.fetchone()
    if results:
        try:
            # checks first for recently generated textfiles if not use gn1 datamatrix

            return __file_scanner__(text_dir, results[0]) or __file_scanner__(TEXTDIR, results[0])

        except Exception:
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
        return (sample_vals, [[line[i] for i in _posit] for line in csv_reader])


def write_db_to_textfile(db_name, conn, text_dir=TMPDIR):

    def __sanitise_filename__(filename):
        ttable = str.maketrans({" ": "_", "/": "_", "\\": "_"})
        return str.translate(filename, ttable)

    def __generate_file_name__(db_name):
        # todo add expiry time and checker
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (db_name,))
            results = cursor.fetchone()
            if (results):
                return __sanitise_filename__(
                    f"ProbeSetFreezeId_{results[0]}_{results[1]}")

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
        file_name = __generate_file_name__(db_name)
        if (results and file_name):
            __write_to_file__(os.path.join(text_dir, file_name),
                              *__parse_to_dict__(results))
