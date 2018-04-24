import uuid
import hashlib
import hmac
from wqflask import app
from utility.logger import getLogger

logger = getLogger(__name__)

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
