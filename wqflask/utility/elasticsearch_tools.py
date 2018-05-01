# Elasticsearch support
#
# Some helpful commands to view the database:
#
# You can test the server being up with
#
#   curl -H 'Content-Type: application/json' http://localhost:9200
#
# List all indices
#
#   curl -H 'Content-Type: application/json' 'localhost:9200/_cat/indices?v'
#
# To see the users index 'table'
#
#   curl http://localhost:9200/users
#
# To list all user ids
#
# curl -H 'Content-Type: application/json' http://localhost:9200/users/local/_search?pretty=true -d '
# {
#     "query" : {
#         "match_all" : {}
#     },
#     "stored_fields": []
# }'
#
# To view a record
#
#   curl -H 'Content-Type: application/json' http://localhost:9200/users/local/_search?pretty=true -d '
#   {
#     "query" : {
#       "match" : { "email_address": "pjotr2017@thebird.nl"}
#     }
#   }'
#
#
# To delete the users index and data (dangerous!)
#
#   curl -XDELETE -H 'Content-Type: application/json' 'localhost:9200/users'


from elasticsearch import Elasticsearch, TransportError
import logging
from time import sleep

from utility.logger import getLogger
logger = getLogger(__name__)

from utility.tools import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT

def test_elasticsearch_connection():
    es = Elasticsearch(['http://'+ELASTICSEARCH_HOST+":"+str(ELASTICSEARCH_PORT)+'/'], verify_certs=True)
    if not es.ping():
        logger.warning("Elasticsearch is DOWN")

def get_elasticsearch_connection():
    """Return a connection to ES. Returns None on failure"""
    logger.info("get_elasticsearch_connection")
    es = None
    try:
        assert(ELASTICSEARCH_HOST)
        assert(ELASTICSEARCH_PORT)
        logger.info("ES HOST",ELASTICSEARCH_HOST)

        es = Elasticsearch([{
            "host": ELASTICSEARCH_HOST, "port": ELASTICSEARCH_PORT
        }]) if (ELASTICSEARCH_HOST and ELASTICSEARCH_PORT) else None

        setup_users_index(es)

        es_logger = logging.getLogger("elasticsearch")
        es_logger.setLevel(logging.INFO)
        es_logger.addHandler(logging.NullHandler())
    except Exception as e:
        logger.error("Failed to get elasticsearch connection", e)
        es = None

    return es

def setup_users_index(es_connection):
    if es_connection:
        index_settings = {
            "properties": {
                "email_address": {
                    "type": "keyword"}}}

        es_connection.indices.create(index='users', ignore=400)
        es_connection.indices.put_mapping(body=index_settings, index="users", doc_type="local")

def get_user_by_unique_column(es, column_name, column_value, index="users", doc_type="local"):
    return get_item_by_unique_column(es, column_name, column_value, index=index, doc_type=doc_type)

def save_user(es, user, user_id):
    es_save_data(es, "users", "local", user, user_id)

def get_item_by_unique_column(es, column_name, column_value, index, doc_type):
    item_details = get_items_by_column(
        es = es, column_name=column_name, column_value=column_value,
        index=index, doc_type=doc_type)

    if len(item_details) > 0:
        return item_details[0]
    else:
        return None

def get_items_by_column(es, column_name, column_value, index, doc_type):
    items = []
    try:
        response = es.search(
            index = index, doc_type = doc_type, body = {
                "query": { "match": { column_name: column_value } }
            })
        if len(response["hits"]["hits"]) > 0:
            items = map(lambda x: x["_source"], response["hits"]["hits"])
    except TransportError as te:
        pass
    return items

def es_save_data(es, index, doc_type, data_item, data_id):
    es.create(index, doc_type, body=data_item, id=data_id)
    sleep(1) # Delay 1 second to allow indexing


def es_update_data(es, index, doc_type, data_item, data_id):
    es.update(index = index, doc_type = doc_type, id=data_id, body = { "doc": data_item})
    sleep(1)

def es_delete_data_by_id(es, index, doc_type, data_id):
    es.delete(index=index, doc_type=doc_type, id=data_id)
    sleep(1)
