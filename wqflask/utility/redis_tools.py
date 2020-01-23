from __future__ import print_function, division, absolute_import

import simplejson as json

import redis # used for collections
Redis = redis.StrictRedis()

import logging

from flask import (render_template, flash)

from utility.logger import getLogger
logger = getLogger(__name__)

def get_user_id(column_name, column_value):
    user_list = Redis.hgetall("users")
    for key in user_list:
        user_ob = json.loads(user_list[key])
        if user_ob[column_name] == column_value:
            return key

    return None

def get_user_by_unique_column(column_name, column_value):
    item_details = None

    user_list = Redis.hgetall("users")
    if column_name != "user_id":
        for key in user_list:
            user_ob = json.loads(user_list[key])
            if user_ob[column_name] == column_value:
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
        #flash("Invalid code: Password reset code does not exist or might have expired!", "error")
