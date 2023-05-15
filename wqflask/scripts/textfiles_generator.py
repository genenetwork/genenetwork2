# database connection
import contextlib
import pickle
import datetime
from argparse import ArgumentParser
from typing import Any, Iterator, Protocol, Tuple
from pathlib import Path
from urllib.parse import urlparse
import MySQLdb as mdb
import lmdb
import os


"""
*script generate both metadata and probeset textfiles 
*manually commonly used datasets

** USage:
load the guix packages refer to issue:

 => https://issues.genenetwork.org/topics/guix-profiles

python3 file_name  sql_uri_path tmp_path 
flags:

    --metadata  to generate metadata files

    -- textfile to generate the probeset strain data


# example  python3 

 python3 meta_data_script.py "mysql://kabui:1234@localhost/db_webqtl" /tmp --textfile
 python3 meta_data_script.py "mysql://kabui:1234@localhost/db_webqtl" /tmp --metadata

python3 meta_data_script.py "mysql://kabui:1234@localhost/db_webqtl" /tmp --metadata  --textfile

"""


#! add to this list or use get_probes_meta to populate


DATASET_NAMES = [
    ("ProbeSet", "HC_M2_0606_P", "mouse"),
    ("ProbeSet", "UMUTAffyExon_0209_RMA", "mouse")
]


def get_probes_meta(sql_uri):

    # if you need to generate for all probes use this note 1000+

    with database_connection(sql_uri) as conn:
        with conn.cursor() as cursor:
            query = "SELECT Id,NAME FROM ProbeSetFreeze"
            cursor.execute(query)
            return cursor.fetchall()


def parse_db_url(sql_uri: str) -> Tuple:
    """function to parse SQL_URI env variable note:there\
    is a default value for SQL_URI so a tuple result is\
    always expected"""
    parsed_db = urlparse(sql_uri)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)


class Connection(Protocol):

    def cursor(self, *args) -> Any:
        """A cursor in which queries may be performed"""
        ...


@contextlib.contextmanager
def database_connection(sql_uri: str = "") -> Iterator[Connection]:
    """Connect to MySQL database."""
    host, user, passwd, db_name, port = parse_db_url(
        sql_uri)

    connection = mdb.connect(db=db_name,
                             user=user,
                             passwd=passwd or '',
                             host=host,
                             port=port or 3306)
    try:
        yield connection
    finally:
        connection.close()


def query_probes_metadata(dataset_type, dataset_name, species, sql_uri):
    """query traits metadata in bulk for probeset"""

    if dataset_type.lower() != "probeset":
        return []
    with database_connection(sql_uri) as conn:
        with conn.cursor() as cursor:
            query = """
                    SELECT ProbeSet.Name,ProbeSet.Chr,ProbeSet.Mb,
                    ProbeSet.Symbol,ProbeSetXRef.mean,
                    CONCAT_WS('; ', ProbeSet.description, ProbeSet.Probe_Target_Description) AS description,
                    ProbeSetXRef.additive,ProbeSetXRef.LRS,Geno.Chr, Geno.Mb
                    FROM ProbeSet INNER JOIN ProbeSetXRef
                    ON ProbeSet.Id=ProbeSetXRef.ProbeSetId
                    INNER JOIN Geno
                    ON ProbeSetXRef.Locus = Geno.Name
                    INNER JOIN Species
                    ON Geno.SpeciesId = Species.Id
                    WHERE Species.Name = %s AND
                    ProbeSetXRef.ProbeSetFreezeId IN (
                      SELECT ProbeSetFreeze.Id
                      FROM ProbeSetFreeze WHERE ProbeSetFreeze.Name = %s)
                """
            cursor.execute(query, (species,) + (dataset_name,))
            return cursor.fetchall()


def get_metadata(dataset_type, dataset_name, species, sql_uri):
    """Retrieve the metadata"""
    def __location__(probe_chr, probe_mb):
        if probe_mb:
            return f"Chr{probe_chr}: {probe_mb:.6f}"
        return f"Chr{probe_chr}: ???"
    return {trait_name: {
        "name": trait_name,
        "view": True,
        "symbol": symbol,
        "dataset": dataset_name,
        "dataset_name": dataset_name,
        "mean": mean,
        "description": description,
        "additive": additive,
        "lrs_score": f"{lrs:3.1f}" if lrs else "",
        "location": __location__(probe_chr, probe_mb),
        "chr": probe_chr,
        "mb": probe_mb,
        "lrs_location": f'Chr{chr_score}: {mb:{".6f" if mb  else ""}}',
        "lrs_chr": chr_score,
        "lrs_mb": mb

    } for trait_name, probe_chr, probe_mb, symbol, mean, description,
        additive, lrs, chr_score, mb
        in query_probes_metadata(dataset_type, dataset_name, species, sql_uri)}


def cache_trait_metadata(dataset_name, dataset_type, data):
    if not data:
        return
    try:
        with lmdb.open(os.path.join(TMPDIR, f"metadata_{dataset_type}"), map_size=500971520) as env:
            with env.begin(write=True) as txn:
                metadata = {
                    "data": data,
                    "creation_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "dataset_name": dataset_name
                }

                txn.put(f"{dataset_name}".encode(), pickle.dumps(metadata))
    except lmdb.Error as error:
        raise error


def __sanitise_filename__(filename):
    ttable = str.maketrans({" ": "_", "/": "_", "\\": "_"})
    return str.translate(filename, ttable)


def __generate_file_name__(db_name, sql_uri):
    # todo add expiry time and checker

    with database_connection(sql_uri) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s', (db_name,))
            results = cursor.fetchone()
            if (results):
                return __sanitise_filename__(
                    f"ProbeSetFreezeId_{results[0]}_{results[1]}")


def write_strains_data(sql_uri, dataset_name: str, data, col_names):

    if data == {}:
        return
    try:
        with lmdb.open(os.path.join(TMPDIR, "Probesets"), map_size=500971520) as env:
            with env.begin(write=True) as txn:
                meta = {
                    "strain_names": col_names,
                    "data": data,
                    "creation_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                txn.put(__generate_file_name__(dataset_name,
                                               sql_uri).encode(), pickle.dumps(meta))

    except lmdb.Error as error:
        raise error


def generate_probes_textfiles(db_name, db_type, sql_uri):

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
    with database_connection(sql_uri) as conn:
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
            return __parse_to_dict__(cursor.fetchall())


def argument_parser():
    parser = ArgumentParser()

    # add maybe dataset,species as args
    parser.add_argument(
        "SQL_URI",
        help="The uri to use to connect to the database",
        type=str)

    parser.add_argument(
        "TMPDIR",
        help="tmpdir to write the metadata to",
        type=str)
    parser.add_argument('--metadata', dest="metadata", action="store_true")
    parser.add_argument('--textfiles', dest='textfiles', action='store_true')

    parser.set_defaults(textfiles=False)
    parser.set_defaults(metadata=False)
    return parser.parse_args()


def run_textfiles_generator(args):
    try:
        for (d_type, dataset_name, _species) in fetch_to_generate_dataset("ProbeSet", "textfile"):
            file_name = __generate_file_name__(dataset_name, args.SQL_URI)
            if not check_file_expiry(os.path.join(
                    args.TMPDIR, "Probesets"), file_name):
                return
            write_strains_data(
                args.SQL_URI, dataset_name, *generate_probes_textfiles(dataset_name, d_type, args.SQL_URI))
    except Exception as error:
        raise error


def run_metadata_files_generator(args):
    for (dataset_type, dataset_name, species) in fetch_to_generate_dataset("ProbeSet", "metadata"):
        try:
            if not check_file_expiry(os.path.join(TMPDIR, f"metadata_{dataset_type}"), dataset_name):
                return

            cache_trait_metadata(dataset_name, dataset_type, get_metadata(
                dataset_type, dataset_name, species, args.SQL_URI))
        except Exception as error:
            raise error


def read_trait_metadata(dataset_name, dataset_type):
    try:
        with lmdb.open(os.path.join(TMPDIR, f"metadata_{dataset_type}"),
                       readonly=True, lock=False) as env:
            with env.begin() as txn:
                db_name = txn.get(dataset_name.encode())
                return (pickle.loads(db_name) if db_name else {})
    except lmdb.Error as error:
        return {}


def check_file_expiry(target_file_path, dataset_name, max_days=20):
    # return true if file has expired

    try:
        with lmdb.open(target_file_path, readonly=True, lock=False) as env:
            with env.begin() as txn:
                dataset = txn.get(dataset_name.encode())
                if dataset:
                    meta = pickle.loads(dataset)
                    creation_date = datetime.datetime.strptime(
                        meta["creation_date"], '%Y-%m-%d %H:%M:%S')
                    return ((datetime.datetime.now() - creation_date).days > max_days)
                return True
    except Exception:
        return True


def fetch_to_generate_dataset(dataset_type, gen_type):
    try:
        with lmdb.open(os.path.join("/tmp", "todolist_generate"), readonly=True, lock=False) as env:
            with env.begin() as txn:
                data = txn.get(f"{gen_type}:{dataset_type}".encode())
                if data:
                    return [result for result in pickle.loads(data).values()]
                return DATASET_NAMES
    except Exception as err:
        return DATASET_NAMES


if __name__ == '__main__':
    args = argument_parser()
    TMPDIR = args.TMPDIR
    if args.metadata:
        run_metadata_files_generator(args)
    if args.textfiles:
        run_textfiles_generator(args)
