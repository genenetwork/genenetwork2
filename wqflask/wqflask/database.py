# Module to initialize sqlalchemy with flask
import os
import sys
from typing import Tuple, Protocol, Any, Iterator
from urllib.parse import urlparse
import importlib
import contextlib

#: type: ignore
import MySQLdb


class Connection(Protocol):
    def cursor(self) -> Any:
        ...


def read_from_pyfile(pyfile: str, setting: str) -> Any:
    orig_sys_path = sys.path[:]
    sys.path.insert(0, os.path.dirname(pyfile))
    module = importlib.import_module(os.path.basename(pyfile).strip(".py"))
    sys.path = orig_sys_path[:]
    return module.__dict__.get(setting)


def sql_uri() -> str:
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


@contextlib.contextmanager
def database_connection() -> Iterator[Connection]:
    """Provide a context manager for opening, closing, and rolling
    back - if supported - a database connection.  Should an error occur,
    and if the table supports transactions, the connection will be
    rolled back.

    """
    host, user, passwd, db_name, port = parse_db_url(sql_uri())
    connection = MySQLdb.connect(
        db=db_name, user=user, passwd=passwd or '', host=host, port=port,
        autocommit=False  # Required for roll-backs
    )
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()
