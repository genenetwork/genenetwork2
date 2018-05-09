import uuid
import datetime
from elasticsearch import TransportError
from wqflask import user_manager
from utility.elasticsearch_tools import (get_elasticsearch_connection,
                                         get_items_by_column, es_save_data,
                                         es_update_data, es_delete_data_by_id,
                                         get_item_by_unique_column)
from utility.logger import getLogger

logger = getLogger(__name__)
index = "collections"
doc_type = "all"

def get_timestamp_string():
    return datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')

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
    try:
        return es_save_data(
            es = get_elasticsearch_connection(),
            index = index, doc_type = doc_type,
            data_item = collection,
            data_id = collection_id)
    except TransportError as te:
        if te.info["error"]["reason"].find('document already exists') >= 0:
            return es_update_data(
                es = get_elasticsearch_connection(),
                index = index, doc_type = doc_type,
                data_item = collection,
                data_id = collection_id)
        else:
            raise te

def delete_collection_by_id(collection_id):
    return es_delete_data_by_id(
        es = get_elasticsearch_connection(), index = index, doc_type = doc_type,
        data_id = collection_id)

def update_changed_timestamp(collection):
    collection["changed_timestamp"] = get_timestamp_string()
    return collection

def add_traits(collection, traits):
    members = collection["members"]
    new_traits = [trait for trait in traits if trait not in members]
    logger.debug("Adding traits to collection", new_traits)
    if len(new_traits) > 0:
        for trait in new_traits:
            members.append(trait)

        collection["members"] = members

    return update_changed_timestamp(collection)

def remove_traits(collection, traits):
    members = collection["members"]
    collection["members"] = [trait for trait in members if trait not in traits]
    return update_changed_timestamp(collection)

def num_members(collection):
    return len(collection["members"])

def get_members(collection):
    return collection["members"]

def get_anon_collection(collection_name, anon_user):
    collections_list = get_collections_by_user_key(anon_user.key)
    collection = [coll for coll in collections_list if coll["name"] == collection_name]
    if len(collection) == 1:
        collection = collection[0]
    else:
        created_timestamp = get_timestamp_string()
        collection = {
            "id": str(uuid.uuid4()),
            "name": collection_name,
            "created_timestamp": created_timestamp,
            "changed_timestamp": created_timestamp,
            "members": [],
            "user_key": anon_user.key}

    return collection
