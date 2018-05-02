from wqflask import user_manager
from utility.elasticsearch_tools import (get_elasticsearch_connection,
                                         get_items_by_column, es_save_data,
                                         es_update_data, es_delete_data_by_id,
                                         get_item_by_unique_column)
from utility.logger import getLogger

logger = getLogger(__name__)
index = "collections"
doc_type = "all"

def process_traits(unprocessed_traits):
    #print("unprocessed_traits are:", unprocessed_traits)
    if isinstance(unprocessed_traits, basestring):
        unprocessed_traits = unprocessed_traits.split(",")

    traits = set()
    for trait in unprocessed_traits:
        #print("trait is:", trait)
        data, _separator, hmac = trait.rpartition(':')
        data = data.strip()
        assert hmac==user_manager.actual_hmac_creation(data), "Data tampering?"
        traits.add(str(data))

    return traits

def get_collections_by_user_key(key, doc_type="all"):
    return get_items_by_column(
        es = get_elasticsearch_connection(),
        column_name = "user_key",
        column_value = key,
        index = "collections",
        doc_type = doc_type)

def get_collection_by_id(collection_id, doc_type="all"):
    return get_item_by_unique_column(
        es = get_elasticsearch_connection(),
        column_name = "id",
        column_value = collection_id,
        index = "collections",
        doc_type = doc_type)

def save_collection(collection_id, collection):
    if collection.is_new:
        return es_save_data(
            es = get_elasticsearch_connection(),
            index = index, doc_type = doc_type,
            data_item = collection.get_data(),
            data_id = collection_id)
    else:
        return es_update_data(
            es = get_elasticsearch_connection(),
            index = index, doc_type = doc_type,
            data_item = collection.get_data(),
            data_id = collection_id)

def delete_collection_by_id(collection_id):
    return es_delete_data_by_id(
        es = get_elasticsearch_connection(), index = index, doc_type = doc_type,
        data_id = collection_id)
