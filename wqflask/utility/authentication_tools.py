from __future__ import absolute_import, print_function, division

import json
import requests

from base import data_set, webqtlConfig

from utility import hmac
from utility.redis_tools import get_redis_conn, get_resource_info, get_resource_id
Redis = get_redis_conn()

from flask import Flask, g, redirect, url_for

import logging
logger = logging.getLogger(__name__ )

def check_resource_availability(dataset, trait_id=None):

    #ZS: Check if super-user - we should probably come up with some way to integrate this into the proxy
    if g.user_session.user_id in Redis.smembers("super_users"):
       return webqtlConfig.SUPER_PRIVILEGES

    response = None

    #At least for now assume temporary entered traits are accessible#At least for now assume temporary entered traits are accessible
    if type(dataset) == str:
        return webqtlConfig.DEFAULT_PRIVILEGES
    if dataset.type == "Temp":
        return webqtlConfig.DEFAULT_PRIVILEGES

    resource_id = get_resource_id(dataset, trait_id)

    if resource_id:
        resource_info = get_resource_info(resource_id)
        if not resource_info:
            return webqtlConfig.DEFAULT_PRIVILEGES
    else:
        return response #ZS: Need to substitute in something that creates the resource in Redis later

    the_url = "http://localhost:8080/available?resource={}&user={}".format(resource_id, g.user_session.user_id)
    try:
        response = json.loads(requests.get(the_url).content)
    except:
        response = resource_info['default_mask']

    if response:
        return response
    else: #ZS: No idea how this would happen, but just in case
        return False

def check_admin(resource_id=None):
    the_url = "http://localhost:8080/available?resource={}&user={}".format(resource_id, g.user_session.user_id)
    try:
        response = json.loads(requests.get(the_url).content)['admin']
    except:
        response = resource_info['default_mask']['admin']

    if 'edit-admins' in response:
        return "edit-admins"
    elif 'edit-access' in response:
        return "edit-access"
    else:
        return "not-admin"

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

def check_owner_or_admin(dataset=None, trait_id=None, resource_id=None):
    if not resource_id:
        if dataset.type == "Temp":
            return "not-admin"
        else:
            resource_id = get_resource_id(dataset, trait_id)

    if g.user_session.user_id in Redis.smembers("super_users"):
        return "owner"

    resource_info = get_resource_info(resource_id)
    if resource_info:
        if g.user_session.user_id == resource_info['owner_id']:
            return "owner"
        else:
            return check_admin(resource_id)

    return "not-admin"