from __future__ import print_function, division, absolute_import

import simplejson as json

import redis # used for collections
Redis = redis.StrictRedis()

import logging

from flask import (render_template, flash)

from utility.logger import getLogger
logger = getLogger(__name__)

def is_redis_available():
    try:
        Redis.ping()
    except:
        return False
    return True

def get_user_id(column_name, column_value):
    user_list = Redis.hgetall("users")
    for key in user_list:
        user_ob = json.loads(user_list[key])
        if column_name in user_ob and user_ob[column_name] == column_value:
            return key

    return None

def get_user_by_unique_column(column_name, column_value):
    item_details = None

    user_list = Redis.hgetall("users")
    if column_name != "user_id":
        for key in user_list:
            user_ob = json.loads(user_list[key])
            if column_name in user_ob and user_ob[column_name] == column_value:
                item_details = user_ob
    else:
        item_details = json.loads(user_list[column_value])

    return item_details

def set_user_attribute(user_id, column_name, column_value):
    user_info = json.loads(Redis.hget("users", user_id))
    user_info[column_name] = column_value

    Redis.hset("users", user_id, json.dumps(user_info))

def get_user_collections(user_id):
    collections = None
    collections = Redis.hget("collections", user_id)

    if collections:
        return json.loads(collections)
    else:
        return []

def save_user(user, user_id):
    Redis.hset("users", user_id, json.dumps(user))

def save_collections(user_id, collections_ob):
    Redis.hset("collections", user_id, collections_ob)

def save_verification_code(user_email, code):
    Redis.hset("verification_codes", code, user_email)

def check_verification_code(code):
    email_address = None
    user_details = None
    email_address = Redis.hget("verification_codes", code)
    return email_address

    if email_address:
        user_details = get_user_by_unique_column('email_address', email_address)
        return user_details
    else:
        return None
        flash("Invalid code: Password reset code does not exist or might have expired!", "error")

def get_user_groups(user_id):
    #ZS: Get the groups where a user is an admin or a member and return lists corresponding to those two sets of groups
    admin_group_ids = []  #ZS: Group IDs where user is an admin
    user_group_ids = []   #ZS: Group IDs where user is a regular user
    groups_list = Redis.hgetall("groups")
    for key in groups_list:
        group_ob = json.loads(groups_list[key])
        group_admins = set(group_ob['admins'])
        group_users = set(group_ob['users'])
        if user_id in group_admins:
            admin_group_ids.append(group_ob['id'])
        elif user_id in group_users:
            user_group_ids.append(group_ob['id'])
        else:
            continue

    return admin_group_ids, user_group_ids
