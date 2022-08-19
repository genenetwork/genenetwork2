# Module to initialize sqlalchemy with flask
import os
import sys
from string import Template
from typing import Tuple
from urllib.parse import urlparse
import importlib

import MySQLdb


def sql_uri():
    """Read the SQL_URI from the environment or settings file."""
    return os.environ.get(
        "SQL_URI", read_from_pyfile(
            os.environ.get(
                "GN2_SETTINGS", os.path.abspath("../etc/default_settings.py")),
            "SQL_URI"))

def parse_db_url(sql_uri: str) -> Tuple:
    """
    Parse SQL_URI env variable from an sql URI
    e.g. 'mysql://user:pass@host_name/db_name'
    """
    parsed_db = urlparse(sql_uri)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)

def database_connection():
    """Returns a database connection"""
    host, user, passwd, db_name, port = parse_db_url(sql_uri())
    return MySQLdb.connect(
        db=db_name, user=user, passwd=passwd, host=host, port=port)
