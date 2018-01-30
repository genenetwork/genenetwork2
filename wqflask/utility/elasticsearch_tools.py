es = None
try:
    from elasticsearch import Elasticsearch, TransportError
    from utility.tools import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT

    es = Elasticsearch([{
        "host": ELASTICSEARCH_HOST
        , "port": ELASTICSEARCH_PORT
    }]) if (ELASTICSEARCH_HOST and ELASTICSEARCH_PORT) else None
except:
    es = None

def get_user_by_unique_column(column_name, column_value):
    user_details = None
    try:
        response = es.search(
            index = "users"
            , doc_type = "local"
            , body = { 
                "query": { "match": { column_name: column_value } } 
            })
        if len(response["hits"]["hits"]) > 0:
            user_details = response["hits"]["hits"][0]["_source"]
    except TransportError as te: 
        pass
    return user_details

def save_user(user, user_id, index="users", doc_type="local"):
    from time import sleep
    es = Elasticsearch([{
        "host": ELASTICSEARCH_HOST
        , "port": ELASTICSEARCH_PORT
    }])
    es.create(index, doc_type, body=user, id=user_id)
    sleep(1) # Delay 1 second to allow indexing
