#! /usr/bin/env python3

"""This script file reads all Probeset Dataset and caches the data in the CACHEDIR"""

import logging
from gn2.wqflask.correlation.pre_computes import write_db_to_textfile
from gn2.base.webqtlConfig import CACHEDIR
from gn_libs.mysqldb import database_connection
from gn2.utility.tools import SQL_URI, assert_writable_dir

# Setup logging
logging.basicConfig(
    filename="write_db_to_textfile.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

assert_writable_dir(CACHEDIR)

def main():
    logging.info("Starting database text file export...")

    with database_connection(SQL_URI) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT Name FROM ProbeSetFreeze")
            db_names = cursor.fetchall()

        for (db_name,) in db_names:
            db_name = db_name.strip()
            logging.info(f"Processing {db_name}...")
            try:
                write_db_to_textfile(db_name, conn, text_dir=CACHEDIR)
                logging.info(f"Finished {db_name}")
            except Exception as e:
                logging.error(f"Error processing {db_name}: {e}", exc_info=True)

    logging.info("All processing complete.")

if __name__ == "__main__":
    main()
