#! /usr/bin/env python3

"""This script file reads all Probeset Dataset and caches the data in
the CACHEDIR.

USAGE:
To check whether the files changed:
   ./generate_correlation_cache.py is-data-modified

To build the cache:
   ./generate_correlation_cache.py build-probeset-cache
"""

import concurrent.futures
import datetime
import hashlib
import logging
import os
import sys
import time
import warnings

import click
import pandas as pd
from gn_libs.mysqldb import database_connection

warnings.simplefilter(action='ignore', category=UserWarning)


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %Z')

# KLUDGE: FIXME: Duplicate of
# `gn2.wqflask.correlation.pre_computes.write_db_to_textfile`.  We
# have it since importing anything from wqflask co-erces asserts,
# thereby forcing one to set environment variables like GN2_PROFILE
# that we don't need for this script.


def write_db_to_textfile(db_name, sql_uri, text_dir="/tmp/gn2/cache"):
    def __sanitise_filename__(filename):
        ttable = str.maketrans({" ": "_", "/": "_", "\\": "_"})
        return str.translate(filename, ttable)

    def __generate_file_name__(db_name):
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT Id, FullName FROM ProbeSetFreeze WHERE Name = %s',
                (db_name,))
            results = cursor.fetchone()
            if (results):
                return __sanitise_filename__(
                    f"ProbeSetFreezeId_{results[0]}_{results[1]}.parquet")

    with database_connection(sql_uri) as conn, conn.cursor() as cursor:
        file_name = __generate_file_name__(db_name)
        file_path = os.path.join(text_dir, file_name)
        query = f"""SELECT ProbeSet.Name AS trait, Strain.Name AS strain,
ProbeSetData.value AS val
FROM ProbeSetXRef
INNER JOIN ProbeSetFreeze ON ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
INNER JOIN ProbeSet ON ProbeSetXRef.ProbeSetId = ProbeSet.Id
INNER JOIN ProbeSetData ON ProbeSetXRef.DataId = ProbeSetData.Id
INNER JOIN Strain ON ProbeSetData.StrainId = Strain.Id
WHERE ProbeSetFreeze.Name = '{db_name}'"""
        data = pd.read_sql(query, conn)
        df_pivoted = data.pivot(index='trait', columns='strain', values='val')
        df_pivoted.index.name = 'ID'
        df_pivoted.to_parquet(file_path, index=True)
        logging.info(f"Wrote data for {db_name} to {file_path}")


def cache_data(i, name, sql_uri, cache_dir):
    result = ""
    start_time = time.perf_counter()
    logging.info(f"#{i+1}. Processing {name}")
    write_db_to_textfile(name, sql_uri, text_dir=cache_dir)
    total_time = datetime.timedelta(seconds=time.perf_counter() - start_time)
    result = f"#{i+1}. {name} took: {total_time} to finish"
    return result


def get_cache_checksum(sql_uri: str) -> str:
    """Get a checksum for the Tables: Strain, ProbeSetFreeze,
    ProbeSet, ProbeSetData, ProbeSetXRef as a single md5 hash"""
    with database_connection(sql_uri) as conn, conn.cursor() as cursor:
        cursor.execute("CHECKSUM Table Strain, ProbeSetFreeze, \
        ProbeSet, ProbeSetData, ProbeSetXRef")
        checksums = [str(checksum) for (_, checksum) in cursor.fetchall()]
        return hashlib.md5(" ".join(checksums).encode("utf-8")).hexdigest()


@click.command(help="Verify checksums and return True when the data has been changed.")
@click.argument("sql_uri")
@click.option("-c", "--cache-dir",
              type=str,
              default="/tmp/gn2/cache",
              show_default=True)
def is_data_modified(sql_uri: str, cache_dir: str):
    """Check whether checksums have changed.  Return a zero exit
    status code when the data has changed; otherwise exit with a 1
    exit status code."""
    checksum_file = os.path.join(cache_dir, "CHECKSUM.txt")
    if not os.path.exists(checksum_file):
        sys.exit(0)
    with open(checksum_file, "r") as _file:
        checksum = _file.read()
        if checksum == get_cache_checksum(sql_uri):
            sys.exit(1)
        sys.exit(0)


@click.command(help="Read all the Probeset data and cache it into CACHEDIR")
@click.argument("sql_uri")
@click.option("-c", "--cache-dir",
              type=str,
              default="/tmp/gn2/cache",
              show_default=True)
def build_probeset_cache(sql_uri: str, cache_dir: str):
    logging.info("Starting database text file export...")
    start_time = time.perf_counter()
    datasets = []
    with database_connection(sql_uri) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT Name FROM ProbeSetFreeze")
        datasets = cursor.fetchall()
        total_datasets = len(datasets)
        logging.info(f"Found {total_datasets} datasets to process")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i, (name,) in enumerate(datasets):
            futures.append(executor.submit(cache_data, i=i, name=name,
                                           sql_uri=sql_uri, cache_dir=cache_dir))
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            logging.info(f"Progress: {i}/{total_datasets} datasets completed")
            logging.info(future.result())

    logging.info(f"Time to build cache: \
{datetime.timedelta(seconds=time.perf_counter() - start_time)}")

    start_time = time.perf_counter()
    logging.info("Writing checksum")
    with open(os.path.join(cache_dir, "CHECKSUM.txt"), "w") as checksum:
        checksum.write(get_cache_checksum(sql_uri))
    logging.info(f"Time to write checksum: \
{datetime.timedelta(seconds=time.perf_counter() - start_time)}")


@click.group()
def cli():
    pass


cli.add_command(is_data_modified)
cli.add_command(build_probeset_cache)


if __name__ == "__main__":
    cli()
