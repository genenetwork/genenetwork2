from __future__ import print_function, division, absolute_import

import uuid
import simplejson as json
import datetime

import redis # used for collections

import logging

from flask import (render_template, flash)

from utility import hmac

from utility.logger import getLogger
logger = getLogger(__name__)

def get_redis_conn():
    Redis = redis.StrictRedis(port=6380)
    return Redis

Redis = get_redis_conn()

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

    if email_address:
        user_details = get_user_by_unique_column('email_address', email_address)
        if user_details:
            return user_details
        else:
            return None
    else:
        return None

def get_user_groups(user_id):
    #ZS: Get the groups where a user is an admin or a member and return lists corresponding to those two sets of groups
    admin_group_ids = []  #ZS: Group IDs where user is an admin
    user_group_ids = []   #ZS: Group IDs where user is a regular user
    groups_list = Redis.hgetall("groups")
    for key in groups_list:
        try:
            group_ob = json.loads(groups_list[key])
            group_admins = set(group_ob['admins'])
            group_members = set(group_ob['members'])
            if user_id in group_admins:
                admin_group_ids.append(group_ob['id'])
            elif user_id in group_members:
                user_group_ids.append(group_ob['id'])
            else:
                continue
        except:
            continue

    admin_groups = []
    user_groups = []
    for the_id in admin_group_ids:
        admin_groups.append(get_group_info(the_id))
    for the_id in user_group_ids:
        user_groups.append(get_group_info(the_id))

    return admin_groups, user_groups

def get_group_info(group_id):
    group_json = Redis.hget("groups", group_id)
    group_info = None
    if group_json:
        group_info = json.loads(group_json)

    return group_info

def get_group_by_unique_column(column_name, column_value):
    """ Get group by column; not sure if there's a faster way to do this """

    matched_groups = []

    all_group_list = Redis.hgetall("groups")
    for key in all_group_list:
        group_info = json.loads(all_group_list[key])
        if column_name == "admins" or column_name == "members": #ZS: Since these fields are lists, search in the list
            if column_value in group_info[column_name]:
                matched_groups.append(group_info)
        else:
            if group_info[column_name] == column_value:
                matched_groups.append(group_info)

    return matched_groups


def create_group(admin_user_ids, member_user_ids = [], group_name = "Default Group Name"):
    group_id = str(uuid.uuid4())
    new_group = {
        "id"    : group_id,
        "admins": admin_user_ids,
        "members" : member_user_ids,
        "name"  : group_name,
        "created_timestamp": datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
        "changed_timestamp": datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
    }

    Redis.hset("groups", group_id, json.dumps(new_group))

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
            group_users = set(group_info["members"])

        for email in user_emails:
            user_id = get_user_id("email_address", email)
            group_users.add(user_id)

        if admins:
            group_info["admins"] = list(group_users)
        else:
            group_info["members"] = list(group_users)

        group_info["changed_timestamp"] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        Redis.hset("groups", group_id, json.dumps(group_info))
        return group_info
    else:
        return None

def remove_users_from_group(user_id, users_to_remove_ids, group_id, user_type = "members"): #ZS: User type is because I assume admins can remove other admins
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
        Redis.hset("groups", group_id, json.dumps(group_info))
        return group_info
    else:
        return None

def get_resources():
    resource_list = Redis.hgetall("resources")
    return resource_list

def get_resource_id(dataset, trait_id=None):
    if dataset.type == "Publish":
        if trait_id:
            resource_id = hmac.hmac_creation("{}:{}:{}".format('dataset-publish', dataset.id, trait_id))
        else:
            return False
    elif dataset.type == "ProbeSet":
        resource_id = hmac.hmac_creation("{}:{}".format('dataset-probeset', dataset.id))
    elif dataset.type == "Geno":
        resource_id = hmac.hmac_creation("{}:{}".format('dataset-geno', dataset.id))
    else:
        return False

    return resource_id

def get_resource_info(resource_id):
    resource_info = Redis.hget("resources", resource_id)
    return json.loads(resource_info)

def add_resource(resource_info):

    if 'trait' in resource_info['data']:
        resource_id = hmac.hmac_creation('{}:{}:{}'.format(str(resource_info['type']), str(resource_info['data']['dataset']), str(resource_info['data']['trait'])))
    else:
        resource_id = hmac.hmac_creation('{}:{}'.format(str(resource_info['type']), str(resource_info['data']['dataset'])))

    Redis.hset("resources", resource_id, json.dumps(resource_info))

    return resource_info
