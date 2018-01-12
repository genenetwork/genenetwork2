from elasticsearch import Elasticsearch, TransportError
from utility.tools import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT

es = Elasticsearch([{
    "host": ELASTICSEARCH_HOST
    , "port": ELASTICSEARCH_PORT
}]) 

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
