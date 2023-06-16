"data_set package utilities"

import datetime
import os
import json
import hashlib
from typing import List

from flask import current_app as app

from utility.configuration import get_setting
from wqflask.database import parse_db_url, database_connection

def geno_mrna_confidentiality(ob):
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT confidentiality, "
            f"AuthorisedUsers FROM {ob.type}Freeze WHERE Name = %s",
            (ob.name,)
        )
        result = cursor.fetchall()
        if len(result) > 0 and result[0]:
            return True

def query_table_timestamp(dataset_type: str):
    """function to query the update timestamp of a given dataset_type"""

    # computation data and actions
    with database_connection() as conn, conn.cursor() as cursor:
        fetch_db_name = parse_db_url(get_setting(app, "SQL_URI"))
        cursor.execute(
            "SELECT UPDATE_TIME FROM "
            "information_schema.tables "
            f"WHERE TABLE_SCHEMA = '{fetch_db_name[3]}' "
            f"AND TABLE_NAME = '{dataset_type}Data'")
        date_time_obj = cursor.fetchone()[0]
        if not date_time_obj:
            date_time_obj = datetime.datetime.now()
        return date_time_obj.strftime("%Y-%m-%d %H:%M:%S")


def generate_hash_file(dataset_name: str, dataset_type: str, dataset_timestamp: str, samplelist: str):
    """given the trait_name generate a unique name for this"""
    string_unicode = f"{dataset_name}{dataset_timestamp}{samplelist}".encode()
    md5hash = hashlib.md5(string_unicode)
    return md5hash.hexdigest()


def cache_dataset_results(dataset_name: str, dataset_type: str, samplelist: List, query_results: List):
    """function to cache dataset query results to file
    input dataset_name and type query_results(already processed in default dict format)
    """
    # data computations actions
    # store the file path on redis

    table_timestamp = query_table_timestamp(dataset_type)
    samplelist_as_str = ",".join(samplelist)

    file_name = generate_hash_file(dataset_name, dataset_type, table_timestamp, samplelist_as_str)
    file_path = os.path.join(app.config["WEBQTL_TMPDIR"], f"{file_name}.json")

    with open(file_path, "w") as file_handler:
        json.dump(query_results, file_handler)


def fetch_cached_results(dataset_name: str, dataset_type: str, samplelist: List):
    """function to fetch the cached results"""

    table_timestamp = query_table_timestamp(dataset_type)
    samplelist_as_str = ",".join(samplelist)

    file_name = generate_hash_file(dataset_name, dataset_type, table_timestamp, samplelist_as_str)
    file_path = os.path.join(app.config["WEBQTL_TMPDIR"], f"{file_name}.json")
    try:
        with open(file_path, "r") as file_handler:

            return json.load(file_handler)

    except Exception:
        pass
