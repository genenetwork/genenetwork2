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

def get_resource_id_by_data(res_type, res_data):
    resource_list = Redis.hgetall("resources")
    for key in resource_list:
        resource_ob = json.loads(resource_list[key])

        logger.info(resource_ob["data"])
        if resource_ob["type"] == res_type and resource_ob["data"] == res_data:
            return key

    return None

def get_resource(resource_id):
    return json.loads(Redis.hget("resources", resource_id))

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

def get_group_info(group_id):
    group_json = Redis.hget("groups", group_id)
    group_info = None
    if group_json:
        group_info = json.loads(group_json)

    return group_info

def create_group(admin_member_ids, user_member_ids = [], group_name = ""):
    group_id = str(uuid.uuid4())
    new_group = {
        "id"    : group_id,
        "admins": admin_member_ids,
        "users" : user_member_ids,
        "name"  : group_name,
        "created_timestamp": datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
        "changed_timestamp": datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
    }

    Redis.hset("groups", group_id, new_group)

    return new_group

def delete_group(user_id, group_id):
    #ZS: If user is an admin of a group, remove it from the groups hash
    group_info = get_group_info(group_id)
    if user_id in group_info["admins"]:
        Redis.hdel("groups", group_id)
        return get_user_groups(user_id)
    else:
        None

def add_users_to_group(user_id, group_id, user_emails = [], admins = False): #ZS "admins" is just to indicate whether the users should be added to the groups admins or regular users set
    group_info = get_group_info(group_id)
    if user_id in group_info["admins"]: #ZS: Just to make sure that the user is an admin for the group, even though they shouldn't be able to reach this point unless they are
        if admins:
            group_users = set(group_info["admins"])
        else:
            group_users = set(group_info["users"])

        for email in user_emails:
            user_id = get_user_id("email_address", email)
            group_users.add(user_id)

        if admins:
            group_info["admins"] = list(group_users)
        else:
            group_info["users"] = list(group_users)

        group_info["changed_timestamp"] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        Redis.hset("groups", group_id, json.dumps(group_info))
        return group_info
    else:
        return None

def remove_users_from_group(user_id, users_to_remove_ids, group_id, user_type = "users"): #ZS: User type is because I assume admins can remove other admins
    group_info = get_group_info(group_id)
    if user_id in group_info["admins"]:
        group_users = set(group_info[user_type])
        group_users -= set(users_to_remove_ids)
        group_info[user_type] = list(group_users)
        group_info["changed_timestamp"] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        Redis.hset("groups", group_id, json.dumps(group_info))

def change_group_name(user_id, group_id, new_name):
    group_info = get_group_info(group_id)
    if user_id in group_info["admins"]:
        group_info["name"] = new_name
        return group_info
    else:
        return None
