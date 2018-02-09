es = None
try:
    from elasticsearch import Elasticsearch, TransportError
    from utility.tools import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT

    es = Elasticsearch([{
        "host": ELASTICSEARCH_HOST
        , "port": ELASTICSEARCH_PORT
    }]) if (ELASTICSEARCH_HOST and ELASTICSEARCH_PORT) else None

    # Check if elasticsearch is running
    if not es.ping():
        es = None
except:
    es = None

def get_user_by_unique_column(column_name, column_value):
    return get_item_by_unique_column(column_name, column_value, index="users", doc_type="local")

def save_user(user, user_id):
    es_save_data("users", "local", user, user_id)

def get_item_by_unique_column(column_name, column_value, index, doc_type):
    item_details = None
    try:
        response = es.search(
            index = index
            , doc_type = doc_type
            , body = { 
                "query": { "match": { column_name: column_value } } 
            })
        if len(response["hits"]["hits"]) > 0:
            item_details = response["hits"]["hits"][0]["_source"]
    except TransportError as te: 
        pass
    return item_details

def es_save_data(index, doc_type, data_item, data_id,):
    from time import sleep
    es.create(index, doc_type, body=data_item, id=data_id)
    sleep(1) # Delay 1 second to allow indexing
