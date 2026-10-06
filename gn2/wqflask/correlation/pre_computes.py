import csv
import json
import os
import hashlib
import datetime
import tempfile

import lmdb
import pickle
from pathlib import Path

from gn2.base.data_set import query_table_timestamp
from gn2.base.webqtlConfig import CACHEDIR

from json.decoder import JSONDecodeError
from gn2.utility.tools import  assert_writable_dir

assert_writable_dir(CACHEDIR)


class MalformedTextFileError(Exception):
    """Raised when a cached text file does not match its own header.

    Cache files are written in one piece, with every row holding a value for
    every sample named in the header.  A row that holds fewer fields means the
    file was written with a different layout, or was only partially written, so
    its values cannot be trusted to line up with the header.
    """


def discard_cached_text_file(file_path):
    """Delete a cached text file so that the caller can regenerate it."""

    try:
        Path(file_path).unlink()
        return True
    except OSError:
        return False


def cache_trait_metadata(dataset_name, data):


    try:
        with lmdb.open(os.path.join(CACHEDIR, f"metadata_{dataset_name}"),map_size=20971520) as env:
            with  env.begin(write=True) as  txn:
                data_bytes = pickle.dumps(data)
                txn.put(f"{dataset_name}".encode(), data_bytes)
                current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                txn.put(b"creation_date", current_date.encode())
                return "success"

    except lmdb.Error as  error:
        pass

def read_trait_metadata(dataset_name):
    try:
        with lmdb.open(os.path.join(CACHEDIR, f"metadata_{dataset_name}"),
            readonly=True, lock=False) as env:
            with env.begin() as txn:
                db_name = txn.get(dataset_name.encode())
                return (pickle.loads(db_name) if db_name else {})
    except lmdb.Error as error:
        return {}


def fetch_all_cached_metadata(dataset_name):
    """in a gvein dataset fetch all the traits metadata"""
    file_name = generate_filename(dataset_name, suffix="metadata")

    file_path = Path(CACHEDIR, file_name)

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


def fetch_text_file(dataset_name, conn, text_dir=CACHEDIR):
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
            return __file_scanner__(text_dir, results[0])

        except Exception:
            pass


def read_text_file(sample_dict, file_path):
    """Read the samples of interest out of a cached dataset text file.

    Every row is checked against the header before its values are used.  A row
    holding fewer fields than the header means the file was not written by the
    code that writes it now, so `MalformedTextFileError` is raised instead of
    silently reading values that line up with the wrong samples.
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

        try:
            header = next(csv_reader)
        except StopIteration as stop:
            raise MalformedTextFileError(
                f"The cached text file '{file_path}' is empty.") from stop

        _posit, sample_vals = __fetch_id_positions__(header[1:], sample_dict)

        # NB: field 0 is the trait id, so a usable row needs one more field than
        # the highest sample position we are going to read.
        required_fields = max(_posit) + 1
        sample_data = []

        for line_number, line in enumerate(csv_reader, 2):
            if len(line) < required_fields:
                raise MalformedTextFileError(
                    f"The cached text file '{file_path}' has {len(line)} "
                    f"fields on line {line_number} but needs at least "
                    f"{required_fields} for its {len(header)}-field header.")

            sample_data.append([line[index] for index in _posit])

        return (sample_vals, sample_data)


def write_db_to_textfile(db_name, sample_list, conn, text_dir=CACHEDIR):

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

    def __parse_to_dict__(results, sample_list):
        data = {}
        # Create a set for faster lookups
        valid_samples = set(sample_list)

        # Initialize traits with "X" for all samples
        for (trait, strain, val) in results:
            if trait not in data:
                data[trait] = {sample: "X" for sample in sample_list}
                data[trait]['ID'] = trait

            # Only update value if strain is in our sample_list
            if strain in valid_samples:
                data[trait][strain] = val

        return data

    def __write_to_file__(file_path, data, sample_list):
        """Write the whole dataset out in one atomic step.

        The file is built under a temporary name in the same directory and only
        moved into place once it is complete, so an interrupted or concurrent
        write can never leave a half-written file behind for `read_text_file`
        to trip over.
        """

        directory = os.path.dirname(file_path) or "."
        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                    mode='w+', encoding='UTF8', dir=directory,
                    prefix='.correlation_cache_', delete=False
            ) as file_handler:
                temporary_path = file_handler.name
                writer = csv.writer(file_handler)
                # Write header - ID column followed by all samples
                header = ['ID'] + sample_list
                writer.writerow(header)

                # Write data rows
                for trait in data:
                    row = [data[trait]['ID']] + [data[trait][sample] for sample in sample_list]
                    writer.writerow(row)

            os.replace(temporary_path, file_path)
        except BaseException:  # pylint: disable=broad-except
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise

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
            parsed_data = __parse_to_dict__(results, sample_list)
            __write_to_file__(os.path.join(text_dir, file_name),
                            parsed_data, sample_list)
