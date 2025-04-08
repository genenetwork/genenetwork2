#! /usr/bin/env python3

"""This script file reads all Probeset Dataset and caches the data in
the CACHEDIR.

USAGE:
To check whether the files changed:
   ./generate_correlation_cache.py is-data-modified

To build the cache:
   ./generate_correlation_cache.py build-probeset-cache
"""

import os
import csv
import time
import datetime
import sys
import logging
import hashlib
import click

from gn_libs.mysqldb import database_connection


# KLUDGE: FIXME: Duplicate of
# `gn2.wqflask.correlation.pre_computes.write_db_to_textfile`.  We
# have it since importing anything from wqflask co-erces asserts,
# thereby forcing one to set environment variables like GN2_PROFILE
# that we don't need for this script.
def write_db_to_textfile(db_name, conn, text_dir="/tmp/gn2/cache"):
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
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %Z')
    logging.info("Starting database text file export...")
    start_time = time.perf_counter()
    with database_connection(sql_uri) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT Name FROM ProbeSetFreeze")
        for (name,) in cursor.fetchall():
            name = name.strip()
            logging.info(f"Processing {name}...")
            try:
                write_db_to_textfile(name, conn, text_dir=cache_dir)
                logging.info(f"Finished {name}")
            except Exception as e:
                logging.error(f"Error processing {name}: {e}", exc_info=True)
    index_time = datetime.timedelta(seconds=time.perf_counter() - start_time)

    with open(os.path.join(cache_dir, "CHECKSUM.txt"), "w") as checksum:
        checksum.write(get_cache_checksum(sql_uri))

    logging.info("Cache files successfully built.")
    logging.info(f"Time to build cache: {index_time}")


@click.group()
def cli():
    pass


cli.add_command(is_data_modified)
cli.add_command(build_probeset_cache)


if __name__ == "__main__":
    cli()
