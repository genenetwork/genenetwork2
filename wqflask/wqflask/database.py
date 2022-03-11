# Module to initialize sqlalchemy with flask
import os
import sys
from string import Template
from typing import Tuple
from urllib.parse import urlparse
import importlib

import MySQLdb

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

def read_from_pyfile(pyfile, setting):
    orig_sys_path = sys.path[:]
    sys.path.insert(0, os.path.dirname(pyfile))
    module = importlib.import_module(os.path.basename(pyfile).strip(".py"))
    sys.path = orig_sys_path[:]
    return module.__dict__.get(setting)

def sql_uri():
    """Read the SQL_URI from the environment or settings file."""
    return os.environ.get(
        "SQL_URI", read_from_pyfile(os.environ.get("GN2_SETTINGS"), "SQL_URI"))

engine = create_engine(sql_uri(), encoding="latin1")

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Initialise the db
Base.metadata.create_all(bind=engine)

def parse_db_url(sql_uri: str) -> Tuple:
    """
    Parse SQL_URI env variable from an sql URI
    e.g. 'mysql://user:pass@host_name/db_name'
    """
    parsed_db = urlparse(sql_uri)
    return (parsed_db.hostname, parsed_db.username,
            parsed_db.password, parsed_db.path[1:])

def database_connection():
    """Returns a database connection"""
    host, user, passwd, db_name = parse_db_url(sql_uri())
    return MySQLdb.Connect(db=db_name, user=user, passwd=passwd, host=host)
