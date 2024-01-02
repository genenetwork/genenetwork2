from gn2.utility.tools import get_setting
from gn2.wqflask.database import database_connection


def escape_(string):
    with database_connection(get_setting("SQL_URI")) as conn:
        return conn.escape_string(str(string))


def create_in_clause(items):
    """Create an in clause for mysql"""
    in_clause = ', '.join("'{}'".format(x) for x in mescape(*items))
    in_clause = '( {} )'.format(in_clause)
    return in_clause


def mescape(*items):
    """Multiple escape"""
    return [escape_(str(item)).decode('utf8') for item in items]


def escape(string_):
    return escape_(string_).decode('utf8')
