from __future__ import print_function, division, absolute_import

import hashlib
import hmac

from wqflask import app

def hmac_creation(stringy):
    """Helper function to create the actual hmac"""

    secret = app.config['SECRET_HMAC_CODE']

    hmaced = hmac.new(secret, stringy, hashlib.sha1)
    hm = hmaced.hexdigest()
    # ZS: Leaving the below comment here to ask Pjotr about
    # "Conventional wisdom is that you don't lose much in terms of security if you throw away up to half of the output."
    # http://www.w3.org/QA/2009/07/hmac_truncation_in_xml_signatu.html
    hm = hm[:20]
    return hm