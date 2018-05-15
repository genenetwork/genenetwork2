import uuid
import hashlib
import datetime
import hmac
from wqflask import app
from flask import request
from utility.logger import getLogger
from utility.elasticsearch_tools import (es_save_data, get_item_by_unique_column,
                                         get_elasticsearch_connection,
                                         es_delete_data_by_id, es_get_all_items)

logger = getLogger(__name__)

cookie_name = 'session_id_v2'

def timestamp():
    return datetime.datetime.utcnow().isoformat()

def verify_cookie(cookie):
    the_uuid, separator, the_signature = cookie.partition(':')
    assert len(the_uuid) == 36, "Is session_id a uuid?"
    assert separator == ":", "Expected a : here"
    assert the_signature == actual_hmac_creation(the_uuid), "Uh-oh, someone tampering with the cookie?"
    return the_uuid

def create_signed_cookie():
    the_uuid = str(uuid.uuid4())
    signature = actual_hmac_creation(the_uuid)
    uuid_signed = the_uuid + ":" + signature
    logger.debug("uuid_signed:", uuid_signed)
    return the_uuid, uuid_signed

def actual_hmac_creation(stringy):
    """Helper function to create the actual hmac"""

    secret = app.config['SECRET_HMAC_CODE']

    hmaced = hmac.new(secret, stringy, hashlib.sha1)
    hm = hmaced.hexdigest()
    # "Conventional wisdom is that you don't lose much in terms of security if you throw away up to half of the output."
    # http://www.w3.org/QA/2009/07/hmac_truncation_in_xml_signatu.html
    hm = hm[:20]
    return hm

def save_cookie_details(cookie_id, user):
    es_save_data(
        es = get_elasticsearch_connection(),
        index = "cookies",
        doc_type = "local",
        data_item = {
            "cookie_id": cookie_id,
            "user": user
        },
        data_id = cookie_id)

def get_cookie_details(cookie_id):
    return get_item_by_unique_column(
        es = get_elasticsearch_connection(), column_name = "cookie_id",
        column_value = cookie_id, index = "cookies", doc_type = "local")

def delete_cookie_details():
    cookie_id = request.cookies.get(cookie_name)
    return es_delete_data_by_id(
        es = get_elasticsearch_connection(), index = "cookies",
        doc_type = "local", data_id=cookie_id)

def get_all_users():
    return es_get_all_items(
        es = get_elasticsearch_connection(),
        index = "users",
        doc_type = "local")
