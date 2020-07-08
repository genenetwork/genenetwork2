"""

Script that sets default resource access masks for use with the DB proxy

Defaults will be:
Owner - omni_gn
Mask  - Public/non-confidential: { data: "view",
                                   metadata: "view",
                                   admin: "not-admin" }
        Private/confidentia:     { data: "no-access",
                                   metadata: "no-access",
                                   admin: "not-admin" }

To run:
./bin/genenetwork2 ~/my_settings.py -c ./wqflask/maintenance/gen_select_dataset.py

"""

from __future__ import print_function, division

import sys
import json

# NEW: Note we prepend the current path - otherwise a guix instance of GN2 may be used instead
sys.path.insert(0,'./')

# NEW: import app to avoid a circular dependency on utility.tools
from wqflask import app

from utility import hmac
from utility.tools import SQL_URI
from utility.redis_tools import get_redis_conn, get_user_id, add_resource, get_resources, get_resource_info
Redis = get_redis_conn()

import MySQLdb

import urlparse

from utility.logger import getLogger
logger = getLogger(__name__)

def parse_db_uri():
    """Converts a database URI to the db name, host name, user name, and password"""

    parsed_uri = urlparse.urlparse(SQL_URI)

    db_conn_info = dict(
                        db = parsed_uri.path[1:],
                        host = parsed_uri.hostname,
                        user = parsed_uri.username,
                        passwd = parsed_uri.password)

    print(db_conn_info)
    return db_conn_info

def insert_probeset_resources(default_owner_id):
    current_resources = Redis.hgetall("resources")
    Cursor.execute("""  SELECT
                            ProbeSetFreeze.Id, ProbeSetFreeze.Name, ProbeSetFreeze.confidentiality, ProbeSetFreeze.public
                        FROM
                            ProbeSetFreeze""")

    resource_results = Cursor.fetchall()
    for i, resource in enumerate(resource_results):
        resource_ob = {}
        resource_ob['name'] = resource[1]
        resource_ob['owner_id'] = default_owner_id
        resource_ob['data'] = { "dataset" : str(resource[0])}
        resource_ob['type'] = "dataset-probeset"
        if resource[2] < 1 and resource[3] > 0:
            resource_ob['default_mask'] = { "data": "view",
                                            "metadata": "view",
                                            "admin": "not-admin"}
        else:
            resource_ob['default_mask'] = { "data": "no-access",
                                            "metadata": "no-access",
                                            "admin": "not-admin"}
        resource_ob['group_masks'] = {}

        add_resource(resource_ob, update=False)

def insert_publish_resources(default_owner_id):
    current_resources = Redis.hgetall("resources")
    Cursor.execute("""  SELECT 
                            PublishXRef.Id, PublishFreeze.Id, InbredSet.InbredSetCode
                        FROM
                            PublishXRef, PublishFreeze, InbredSet, Publication
                        WHERE
                            PublishFreeze.InbredSetId = PublishXRef.InbredSetId AND
                            InbredSet.Id = PublishXRef.InbredSetId AND
                            Publication.Id = PublishXRef.PublicationId""")

    resource_results = Cursor.fetchall()
    for resource in resource_results:
        if resource[2]:
            resource_ob = {}
            if resource[2]:
                resource_ob['name'] = resource[2] + "_" + str(resource[0])
            else:
                resource_ob['name'] = str(resource[0])
            resource_ob['owner_id'] = default_owner_id
            resource_ob['data'] = { "dataset" : str(resource[1]) ,
                                    "trait"   : str(resource[0])}
            resource_ob['type'] = "dataset-publish"
            resource_ob['default_mask'] = { "data": "view",
                                            "metadata": "view",
                                            "admin": "not-admin"}

            resource_ob['group_masks'] = {}

            add_resource(resource_ob, update=False)
        else:
            continue

def insert_geno_resources(default_owner_id):
    current_resources = Redis.hgetall("resources")
    Cursor.execute("""  SELECT
                            GenoFreeze.Id, GenoFreeze.ShortName, GenoFreeze.confidentiality
                        FROM
                            GenoFreeze""")

    resource_results = Cursor.fetchall()
    for i, resource in enumerate(resource_results):
        resource_ob = {}
        resource_ob['name'] = resource[1]
        if resource[1] == "HET3-ITPGeno":
            resource_ob['owner_id'] = "c5ce8c56-78a6-474f-bcaf-7129d97f56ae"
        else:
            resource_ob['owner_id'] = default_owner_id
        resource_ob['data'] = { "dataset" : str(resource[0]) }
        resource_ob['type'] = "dataset-geno"
        if resource[2] < 1:
            resource_ob['default_mask'] = { "data": "view",
                                            "metadata": "view",
                                            "admin": "not-admin"}
        else:
            resource_ob['default_mask'] = { "data": "no-access",
                                            "metadata": "no-access",
                                            "admin": "not-admin"}
        resource_ob['group_masks'] = {}

        add_resource(resource_ob, update=False)

def insert_resources(default_owner_id):
    current_resources = get_resources()
    print("START")
    insert_publish_resources(default_owner_id)
    print("AFTER PUBLISH")
    insert_geno_resources(default_owner_id)
    print("AFTER GENO")
    insert_probeset_resources(default_owner_id)
    print("AFTER PROBESET")

def main():
    """Generates and outputs (as json file) the data for the main dropdown menus on the home page"""

    Redis.delete("resources")

    owner_id = "c5ce8c56-78a6-474f-bcaf-7129d97f56ae"

    insert_resources(owner_id)

if __name__ == '__main__':
    Conn = MySQLdb.Connect(**parse_db_uri())
    Cursor = Conn.cursor()
    main()