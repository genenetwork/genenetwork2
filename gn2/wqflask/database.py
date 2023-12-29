# Module to initialize sqlalchemy with flask
import os
import sys
import logging
import traceback
from typing import Tuple, Protocol, Any, Iterator
from urllib.parse import urlparse
import importlib
import contextlib

#: type: ignore
import MySQLdb


class Connection(Protocol):
    def cursor(self) -> Any:
        ...

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
def database_connection(sql_uri: str) -> Iterator[Connection]:
    """Provide a context manager for opening, closing, and rolling
    back - if supported - a database connection.  Should an error occur,
    and if the table supports transactions, the connection will be
    rolled back.

    """
    host, user, passwd, db_name, port = parse_db_url(sql_uri)
    connection = MySQLdb.connect(
        db=db_name, user=user, passwd=passwd or '', host=host,
        port=(port or 3306), autocommit=False  # Required for roll-backs
    )
    try:
        yield connection
        connection.commit()
    except Exception as _exc:
        logging.error("===== Query Error =====\r\n%s\r\n===== END: Query Error",
                      traceback.format_exc())
        connection.rollback()
        raise _exc
    finally:
        connection.close()
