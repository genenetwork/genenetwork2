import json
import requests

from base import data_set, webqtlConfig

from utility import hmac
from utility.redis_tools import get_redis_conn, get_resource_info, get_resource_id, add_resource
Redis = get_redis_conn()

from flask import Flask, g, redirect, url_for

import logging
logger = logging.getLogger(__name__ )

def check_resource_availability(dataset, trait_id=None):

    #At least for now assume temporary entered traits are accessible
    if isinstance(dataset, str):
        return webqtlConfig.DEFAULT_PRIVILEGES
    if dataset.type == "Temp":
        return webqtlConfig.DEFAULT_PRIVILEGES

    resource_id = get_resource_id(dataset, trait_id)

    if resource_id: #ZS: This should never be false, but it's technically possible if a non-Temp dataset somehow had a type other than Publish/ProbeSet/Geno
        resource_info = get_resource_info(resource_id)
        if not resource_info: #ZS: If resource isn't already in redis, add it with default privileges
            resource_info = add_new_resource(dataset, trait_id)

    #ZS: Check if super-user - we should probably come up with some way to integrate this into the proxy
    if g.user_session.user_id in Redis.smembers("super_users"):
       return webqtlConfig.SUPER_PRIVILEGES

    response = None

    the_url = "http://localhost:8080/available?resource={}&user={}".format(resource_id, g.user_session.user_id)
    try:
        response = json.loads(requests.get(the_url).content)
    except:
        response = resource_info['default_mask']

    return response

def add_new_resource(dataset, trait_id=None):
    resource_ob = {
        'owner_id'    : "none", # webqtlConfig.DEFAULT_OWNER_ID,
        'default_mask': webqtlConfig.DEFAULT_PRIVILEGES,
        'group_masks' : {}
    }

    if dataset.type == "Publish":
        group_code = get_group_code(dataset)
        if group_code is None:
            group_code = ""
        resource_ob['name'] = group_code + "_" + str(trait_id)
        resource_ob['data'] = {
            'dataset': dataset.id,
            'trait'  : trait_id
        }
        resource_ob['type'] = 'dataset-publish'
    elif dataset.type == "Geno":
        resource_ob['name'] = dataset.name
        resource_ob['data'] = {
            'dataset': dataset.id
        }
        resource_ob['type'] = 'dataset-geno'
    else:
        resource_ob['name'] = dataset.name
        resource_ob['data'] = {
            'dataset': dataset.id
        }
        resource_ob['type'] = 'dataset-probeset'

    resource_info = add_resource(resource_ob, update=False)

    return resource_info

def get_group_code(dataset):
    results = g.db.execute("SELECT InbredSetCode from InbredSet where Name='{}'".format(dataset.group.name)).fetchone()
    if results[0]:
        return results[0]
    else:
        return ""

def check_admin(resource_id=None):
    the_url = "http://localhost:8080/available?resource={}&user={}".format(resource_id, g.user_session.user_id)
    try:
        response = json.loads(requests.get(the_url).content)['admin']
    except:
        resource_info = get_resource_info(resource_id)
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
