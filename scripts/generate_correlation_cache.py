#! /usr/bin/env python3

"""This script file reads all Probeset Dataset and caches the data in the CACHEDIR"""

import os
import time
import datetime
import sys
import logging
import click
import hashlib

from gn2.wqflask.correlation.pre_computes import write_db_to_textfile
from gn2.base.webqtlConfig import CACHEDIR
from gn_libs.mysqldb import database_connection
from gn2.utility.tools import SQL_URI, assert_writable_dir


assert_writable_dir(CACHEDIR)


def get_cache_checksum():
    """Get a checksum for the Tables: Strain, ProbeSetFreeze,
    ProbeSet, ProbeSetData, ProbeSetXRef as a single md5 hash"""
    with database_connection(SQL_URI) as conn, conn.cursor() as cursor:
        cursor.execute("CHECKSUM Table Strain, ProbeSetFreeze, \
        ProbeSet, ProbeSetData, ProbeSetXRef")
        checksums = [str(checksum) for (_, checksum) in cursor.fetchall()]
        return hashlib.md5(" ".join(checksums).encode("utf-8")).hexdigest()


@click.command(help="Verify checksums and return True when the data has been changed.")
def is_data_modified():
    """Check whether checksums have changed.  Return a zero exit
    status code when the data has changed; otherwise exit with a 1
    exit status code."""
    checksum_file = os.path.join(CACHEDIR, "CHECKSUM.txt")
    if not os.path.exists(checksum_file):
        sys.exit(0)
    with open(checksum_file, "r") as _file:
        checksum = _file.read()
        if checksum == get_cache_checksum():
            sys.exit(1)
        sys.exit(0)


@click.command(help="Read all the Probeset data and cache it into CACHEDIR")
def build_probeset_cache():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %Z')
    logging.info("Starting database text file export...")
    start_time = time.perf_counter()
    with database_connection(SQL_URI) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT Name FROM ProbeSetFreeze")

        for (name,) in cursor.fetchall():
            name = name.strip()
            logging.info(f"Processing {name}...")
            try:
                write_db_to_textfile(name, conn, text_dir=CACHEDIR)
                logging.info(f"Finished {name}")
            except Exception as e:
                logging.error(f"Error processing {name}: {e}", exc_info=True)
    index_time = datetime.timedelta(seconds=time.perf_counter() - start_time)

    with open(os.path.join(CACHEDIR, "CHECKSUM.txt"), "w") as checksum:
        checksum.write(get_cache_checksum())

    logging.info("Cache files successfully built.")
    logging.info(f"Time to build cache: {index_time}")


@click.group()
def cli():
    pass


cli.add_command(is_data_modified)
cli.add_command(build_probeset_cache)


if __name__ == "__main__":
    cli()
