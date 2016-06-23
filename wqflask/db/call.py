# Module for calling the backend

from flask import g

# import MySQLdb
import string
import urllib2
import json
# from base import webqtlConfig
from utility.tools import USE_GN_SERVER, LOG_SQL
from utility.benchmark import Bench

from utility.logger import getLogger
logger = getLogger(__name__ )

from inspect import stack

def fetchone(query):
    """Return tuple containing one row by calling SQL directly

    """
    with Bench("SQL",LOG_SQL):
        def helper(query):
            res = g.db.execute(query)
            return res.fetchone()
        callername = stack()[1][3]
        return logger.sql(callername, query, helper)

def gn_server(path):
    """Return JSON record by calling GN_SERVER

    """
    with Bench("GN_SERVER",LOG_SQL):
        res = urllib2.urlopen("http://localhost:8880/"+path)
        rest = res.read()
        res2 = json.loads(rest)
        logger.info(res2)
        return res2
