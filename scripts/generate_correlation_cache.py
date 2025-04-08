#! /usr/bin/env python3

"""This script file reads all Probeset Dataset and caches the data in the CACHEDIR"""

import os
import logging
import click

from gn2.wqflask.correlation.pre_computes import write_db_to_textfile
from gn2.base.webqtlConfig import CACHEDIR
from gn_libs.mysqldb import database_connection
from gn2.utility.tools import SQL_URI, assert_writable_dir


assert_writable_dir(CACHEDIR)


@click.command(help="Read all the Probeset data and cache it into CACHEDIR")
def build_probeset_cache():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %Z')
    logging.info("Starting database text file export...")

    with database_connection(SQL_URI) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT Name FROM ProbeSetFreeze")
            probeset_datasets = cursor.fetchall()

        for (name,) in probeset_datasets:
            name = name.strip()
            logging.info(f"Processing {name}...")
            try:
                write_db_to_textfile(name, conn, text_dir=CACHEDIR)
                logging.info(f"Finished {name}")
            except Exception as e:
                logging.error(f"Error processing {name}: {e}", exc_info=True)

    logging.info("All processing complete.")


@click.group()
def cli():
    pass


cli.add_command(build_probeset_cache)


if __name__ == "__main__":
    cli()
