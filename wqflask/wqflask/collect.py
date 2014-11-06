from __future__ import print_function, division, absolute_import


import os
import hashlib
import datetime
import time

import uuid
import hashlib
import hmac
import base64

import urlparse

import simplejson as json

from sqlalchemy import orm

#from redis import StrictRedis
import redis
Redis = redis.StrictRedis()


from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, jsonify)

from wqflask import app


from pprint import pformat as pf


from wqflask.database import db_session

from wqflask import model

from utility import Bunch, Struct
from utility.formatting import numify

from wqflask import user_manager


from base import trait


def get_collection():
    if g.user_session.logged_in:
        return UserCollection()
    else:
        return AnonCollection()
    #else:
    #    CauseError

class AnonCollection(object):
    """User is not logged in"""
    def __init__(self):
        self.anon_user = user_manager.AnonUser()
        self.key = "anon_collection:v4:{}".format(self.anon_user.anon_id)
    
    def add_traits(self, params, collection_name):
        assert collection_name == "Default", "Unexpected collection name for anonymous user"
        print("params[traits]:", params['traits'])
        traits = process_traits(params['traits'])
        print("traits is:", traits)
        print("self.key is:", self.key)
        len_before = len(Redis.smembers(self.key))
        Redis.sadd(self.key, *list(traits))
        Redis.expire(self.key, 60 * 60 * 24 * 3)
        print("currently in redis:", Redis.smembers(self.key))
        len_now = len(Redis.smembers(self.key))
        report_change(len_before, len_now)
        
    def remove_traits(self, params):
        traits_to_remove = params.getlist('traits[]')
        print("traits_to_remove:", traits_to_remove)
        len_before = len(Redis.smembers(self.key))
        Redis.srem(self.key, traits_to_remove)
        len_now = len(Redis.smembers(self.key))
        print("Went from {} to {} members in set.".format(len(self.collection_members), len(members_now)))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len(members_now))
    
    def get_traits(self):
        traits = Redis.smembers(self.key)
        print("traits:", traits)
        return traits
    
class UserCollection(object):
    """User is logged in"""
    
    def add_traits(self, params, collection_name):
        print("---> params are:", params.keys())
        print("     type(params):", type(params))
        if collection_name=="Default":
            uc = g.user_session.user_ob.get_collection_by_name("Default")
            # Doesn't exist so we'll create it
            if not uc:
                return create_new("Default")
        else:
            uc = model.UserCollection.query.get(params['existing_collection'])
        members =  uc.members_as_set() #set(json.loads(uc.members))
        len_before = len(members)
    
        traits = process_traits(params['traits'])
    
        members_now = list(members | traits)
        len_now = len(members_now)
        uc.members = json.dumps(members_now)
    
        uc.changed_timestamp = datetime.datetime.utcnow()
    
        db_session.commit()
    
        print("added to existing, now set is:" + str(uc.members))
        report_change(len_before, len_now)
        
        # Probably have to change that
        return redirect(url_for('view_collection', uc_id=uc.id))
    
    def remove_traits(self, params):
    
        #params = request.form
        print("params are:", params)
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        traits_to_remove = params.getlist('traits[]')
        print("traits_to_remove are:", traits_to_remove)
        traits_to_remove = process_traits(traits_to_remove)
        print("\n\n  after processing, traits_to_remove:", traits_to_remove)
        all_traits = uc.members_as_set()
        print("  all_traits:", all_traits)
        members_now = all_traits - traits_to_remove
        print("  members_now:", members_now)
        print("Went from {} to {} members in set.".format(len(all_traits), len(members_now)))
        uc.members = json.dumps(list(members_now))
        uc.changed_timestamp = datetime.datetime.utcnow()
        db_session.commit()
    
        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len(members_now))
    
def report_change(len_before, len_now):
    new_length = len_now - len_before
    if new_length:
        print("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
    else:
        print("No new traits were added.")




@app.route("/collections/add")
def collections_add():
    traits=request.args['traits']

    if g.user_session.logged_in:
        user_collections = g.user_session.user_ob.user_collections
        print("user_collections are:", user_collections)
        return render_template("collections/add.html",
                               traits=traits,
                               user_collections = user_collections,
                               )
    else:
        return render_template("collections/add_anonymous.html",
                               traits=traits
                               )


@app.route("/collections/new")
def collections_new():
    params = request.args
    print("request.args in collections_new are:", params)

    if "anonymous_add" in params:
        AnonCollection().add_traits(params, "Default")
        return redirect(url_for('view_collection'))

    collection_name = params['new_collection']

    if "create_new" in params:
        print("in create_new")
        return create_new(collection_name)
    elif "add_to_existing" in params:
        print("in add to existing")
        return UserCollection().add_traits(params, collection_name)
    else:
        print("ELSE")
        CauseAnError


def process_traits(unprocessed_traits):
    print("unprocessed_traits are:", unprocessed_traits)
    if isinstance(unprocessed_traits, basestring):
        unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
        print("trait is:", trait)
        data, _separator, hmac = trait.rpartition(':')
        data = data.strip()
        print("data is:", data)
        print("hmac is:", hmac)
        assert hmac==user_manager.actual_hmac_creation(data), "Data tampering?"
        traits.add(str(data))
    return traits

def create_new(collection_name):
    params = request.args
    uc = model.UserCollection()
    uc.name = collection_name
    print("user_session:", g.user_session.__dict__)
    uc.user = g.user_session.user_id
    unprocessed_traits = params['traits']

    traits = process_traits(unprocessed_traits)

    uc.members = json.dumps(list(traits))
    print("traits are:", traits)

    db_session.add(uc)
    db_session.commit()

    print("Created: " + uc.name)
    return redirect(url_for('view_collection', uc_id=uc.id))

@app.route("/collections/list")
def list_collections():
    params = request.args
    try:
        user_collections = list(g.user_session.user_ob.user_collections)
        print("user_collections are:", user_collections)
        return render_template("collections/list.html",
                               params = params,
                               user_collections = user_collections,
                               )
    except:
        return render_template("collections/not_logged_in.html",
                                params = params)


@app.route("/collections/remove", methods=('POST',))
def remove_traits():

    params = request.form
    print("params are:", params)
    uc_id = params['uc_id']
    uc = model.UserCollection.query.get(uc_id)
    traits_to_remove = params.getlist('traits[]')
    print("traits_to_remove are:", traits_to_remove)
    traits_to_remove = process_traits(traits_to_remove)
    print("\n\n  after processing, traits_to_remove:", traits_to_remove)
    all_traits = uc.members_as_set()
    print("  all_traits:", all_traits)
    members_now = all_traits - traits_to_remove
    print("  members_now:", members_now)
    print("Went from {} to {} members in set.".format(len(all_traits), len(members_now)))
    uc.members = json.dumps(list(members_now))
    uc.changed_timestamp = datetime.datetime.utcnow()
    db_session.commit()

    # We need to return something so we'll return this...maybe in the future
    # we can use it to check the results
    return str(len(members_now))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    params = request.form
    print("params:", params)
    uc_id = params['uc_id']
    uc = model.UserCollection.query.get(uc_id)
    # Todo: For now having the id is good enough since it's so unique
    # But might want to check ownership in the future
    collection_name = uc.name
    db_session.delete(uc)
    db_session.commit()
    flash("We've deletet the collection: {}.".format(collection_name), "alert-info")

    return redirect(url_for('list_collections'))


@app.route("/collections/view")
def view_collection():
    params = request.args
    print("params in view collection:", params)
    
    if "uc_id" in params:
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        traits = json.loads(uc.members)
        print("traits are:", traits)
    else:
        traits = AnonCollection().get_traits()

    print("in view_collection traits are:", traits)

    trait_obs = []
    json_version = []

    for atrait in traits:
        print("atrait is:", atrait)
        name, dataset_name = atrait.split(':')

        trait_ob = trait.GeneralTrait(name=name, dataset_name=dataset_name)
        trait_ob.get_info()
        trait_obs.append(trait_ob)

        json_version.append(trait_ob.jsonable())
        #json_version.append(dict(name=trait_ob.name,
        #                         description=trait_ob.description_display,
        #                         location=trait_ob.location_repr,
        #                         mean=trait_ob.mean,
        #                         lrs_score=trait_ob.LRS_score_repr,
        #                         lrs_location=trait_ob.LRS_location_repr))
        #                         dis=trait_ob.description))
        #json_version.append(trait_ob.__dict__th)
        
    collection_info = dict(trait_obs=trait_obs,
                           uc = uc)
    #collection_info = dict(trait_obs=trait_obs)
    if "json" in params:
        print("json_version:", json_version)
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html",
                           **collection_info
                           )
