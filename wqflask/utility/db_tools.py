from __future__ import absolute_import, print_function, division

from MySQLdb import escape_string as escape

def create_in_clause(items):
    """Create an in clause for mysql"""
    in_clause = ', '.join("'{}'".format(x) for x in mescape(*items))
    in_clause = '( {} )'.format(in_clause)
    return in_clause

def mescape(*items):
    """Multiple escape"""
    escaped = [escape(str(item)) for item in items]
    #print("escaped is:", escaped)
    return escaped
