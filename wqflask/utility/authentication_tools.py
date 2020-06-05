from __future__ import absolute_import, print_function, division

import json
import requests

from base import data_set

from utility import hmac
from utility.redis_tools import get_redis_conn, get_resource_info, get_resource_id

from flask import Flask, g, redirect, url_for

import logging
logger = logging.getLogger(__name__ )

def check_resource_availability(dataset, trait_id=None):
    resource_id = get_resource_id(dataset, trait_id)

    if resource_id:
        the_url = "http://localhost:8080/available?resource={}&user={}".format(resource_id, g.user_session.user_id)
        try:
            response = json.loads(requests.get(the_url).content)['data']
        except:
            resource_info = get_resource_info(resource_id)
            response = resource_info['default_mask']['data']

        if 'view' in response:
            return True
        else:
            return redirect(url_for("no_access_page"))

    return True

def check_owner(dataset=None, trait_id=None, resource_id=None):
    if resource_id:
        resource_info = get_resource_info(resource_id)
        if g.user_session.user_id == resource_info['owner_id']:
            return resource_id
    else:
        resource_id = get_resource_id(dataset, trait_id)
        if resource_id:
            resource_info = get_resource_info(resource_id)
            if g.user_session.user_id == resource_info['owner_id']:
                return resource_id

    return False