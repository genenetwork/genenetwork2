# Module for calling the backend

from flask import g

import string
import urllib.request, urllib.error, urllib.parse
import json
from utility.tools import USE_GN_SERVER, LOG_SQL, GN_SERVER_URL
from utility.benchmark import Bench

from utility.logger import getLogger
logger = getLogger(__name__ )

# from inspect import stack

def fetch1(query, path=None, func=None):
    """Fetch one result as a Tuple using either a SQL query or the URI
path to GN_SERVER (when USE_GN_SERVER is True). Apply func to
GN_SERVER result when set (which should return a Tuple)

    """
    if USE_GN_SERVER and path:
        result = gn_server(path)
        if func != None:
            res2 = func(result)
        else:
            res2 = result,
        if LOG_SQL:
            logger.debug("Replaced SQL call",query)
        logger.debug(path,res2)
        return res2
    else:
        return fetchone(query)

def fetchone(query):
    """Return tuple containing one row by calling SQL directly (the
original fetchone, but with logging)

    """
    with Bench("SQL",LOG_SQL):
        def helper(query):
            res = g.db.execute(query)
            return res.fetchone()
        return logger.sql(query, helper)

def fetchall(query):
    """Return row iterator by calling SQL directly (the
original fetchall, but with logging)

    """
    with Bench("SQL",LOG_SQL):
        def helper(query):
            res = g.db.execute(query)
            return res.fetchall()
        return logger.sql(query, helper)

def gn_server(path):
    """Return JSON record by calling GN_SERVER

    """
    with Bench("GN_SERVER",LOG_SQL):
        res = urllib.request.urlopen(GN_SERVER_URL+path)
        rest = res.read()
        res2 = json.loads(rest)
        logger.debug(res2)
        return res2
