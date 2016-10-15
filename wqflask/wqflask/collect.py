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

import redis
Redis = redis.StrictRedis()

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, jsonify)

from wqflask import app

from pprint import pformat as pf

from wqflask.database import db_session

from wqflask import model
from wqflask import user_manager

from utility import Bunch, Struct
from utility.formatting import numify

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
    def __init__(self, collection_name):
        anon_user = user_manager.AnonUser()
        self.key = anon_user.key
        self.name = collection_name
        self.id = None
        self.created_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        self.changed_timestamp = self.created_timestamp #ZS: will be updated when changes are made

        #ZS: Find id and set it if the collection doesn't already exist
        if Redis.get(self.key) == "None" or Redis.get(self.key) == None:
            Redis.set(self.key, None) #ZS: For some reason I get the error "Operation against a key holding the wrong kind of value" if I don't do this
        else:
            collections_list = json.loads(Redis.get(self.key))
            collection_position = 0 #ZS: Position of collection in collection_list, if it exists
            collection_exists = False
            for i, collection in enumerate(collections_list):
                if collection['name'] == self.name:
                    collection_position = i
                    collection_exists = True
                    self.id = collection['id']
                    break

        if self.id == None:
            self.id = str(uuid.uuid4())

    def get_members(self):
        traits = []
        collections_list = json.loads(Redis.get(self.key))
        for collection in collections_list:
            if collection['id'] == self.id:
                traits = collection['members']
        return traits

    @property
    def num_members(self):
        num_members = 0
        collections_list = json.loads(Redis.get(self.key))
        for collection in collections_list:
            if collection['id'] == self.id:
                num_members = collection['num_members']
        return num_members

    def add_traits(self, params):
        #assert collection_name == "Default", "Unexpected collection name for anonymous user"
        self.traits = list(process_traits(params['traits']))
        #len_before = len(Redis.smembers(self.key))
        existing_collections = Redis.get(self.key)
        print("existing_collections:", existing_collections)
        if existing_collections != None and existing_collections != "None":
            collections_list = json.loads(existing_collections)
            collection_position = 0 #ZS: Position of collection in collection_list, if it exists
            collection_exists = False
            for i, collection in enumerate(collections_list):
                if collection['id'] == self.id:
                    collection_position = i
                    collection_exists = True
                    break
            if collection_exists:
                collections_list[collection_position]['members'].extend(self.traits)
                collections_list[collection_position]['num_members'] = len(collections_list[collection_position]['members'])
                collections_list[collection_position]['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
            else:
                collection_dict = {"id" : self.id,
                                   "name" : self.name,
                                   "created_timestamp" : self.created_timestamp,
                                   "changed_timestamp" : self.changed_timestamp,
                                   "num_members" : len(self.traits),
                                   "members" : self.traits}
                collections_list.append(collection_dict)
        else:
            collections_list = []
            collection_dict = {"id" : self.id,
                               "name" : self.name,
                               "created_timestamp" : self.created_timestamp,
                               "changed_timestamp" : self.changed_timestamp,
                               "num_members" : len(self.traits),
                               "members" : self.traits}
            collections_list.append(collection_dict)

        Redis.set(self.key, json.dumps(collections_list))
        #Redis.sadd(self.key, *list(traits))
        #Redis.expire(self.key, 60 * 60 * 24 * 5)
        #len_now = len(Redis.smembers(self.key))
        #report_change(len_before, len_now)

    def remove_traits(self, params):
        traits_to_remove = [(":").join(trait.split(":")[:2]) for trait in params.getlist('traits[]')]
        existing_collections = Redis.get(self.key)
        collection_position = 0
        collections_list = json.loads(existing_collections)
        for i, collection in enumerate(collections_list):
            if collection['id'] == self.id:
                collection_position = i
                collection_exists = True
                break
        collections_list[collection_position]['members'] = [trait for trait in collections_list[collection_position]['members'] if trait not in traits_to_remove]
        collections_list[collection_position]['num_members'] = len(collections_list[collection_position]['members'])
        collections_list[collection_position]['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        len_now = collections_list[collection_position]['num_members']
        #print("before in redis:", json.loads(Redis.get(self.key)))
        Redis.set(self.key, json.dumps(collections_list))
        #print("currently in redis:", json.loads(Redis.get(self.key)))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len_now)


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
            uc = model.UserCollection.query.get(params['existing_collection'].split(":")[0])
        members =  list(uc.members_as_set()) #set(json.loads(uc.members))
        len_before = len(members)

        traits = process_traits(params['traits'])

        members_now = members
        for trait in traits:
            if trait in members:
                continue
            else:
                members_now.append(trait)

        #members_now = list(members | traits)
        len_now = len(members_now)
        uc.members = json.dumps(members_now)

        uc.changed_timestamp = datetime.datetime.utcnow()

        db_session.commit()

        print("added to existing, now set is:" + str(uc.members))
        report_change(len_before, len_now)

        # Probably have to change that
        return redirect(url_for('view_collection', uc_id=uc.id))

def process_traits(unprocessed_traits):
    #print("unprocessed_traits are:", unprocessed_traits)
    if isinstance(unprocessed_traits, basestring):
        unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
        #print("trait is:", trait)
        data, _separator, hmac = trait.rpartition(':')
        data = data.strip()
        assert hmac==user_manager.actual_hmac_creation(data), "Data tampering?"
        traits.add                                                                                               (str(data))
    return traits

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
                               traits = traits,
                               collections = user_collections,
                               )
    else:
        anon_collections = user_manager.AnonUser().get_collections()
        collection_names = []
        for collection in anon_collections:
            collection_names.append({'id':collection['id'], 'name':collection['name']})
        return render_template("collections/add.html",
                                traits = traits,
                                collections = collection_names,
                              )

@app.route("/collections/new")
def collections_new():
    params = request.args

    if "sign_in" in params:
        return redirect(url_for('login'))

    if "create_new" in params:
        print("in create_new")
        collection_name = params['new_collection']
        return create_new(collection_name)
    elif "add_to_existing" in params:
        print("in add to existing")
        collection_name = params['existing_collection'].split(":")[1]
        if g.user_session.logged_in:
            return UserCollection().add_traits(params, collection_name)
        else:
            ac = AnonCollection(collection_name)
            ac.add_traits(params)
            return redirect(url_for('view_collection', collection_id=ac.id))
    else:
        CauseAnError

def create_new(collection_name):
    params = request.args

    unprocessed_traits = params['traits']
    traits = process_traits(unprocessed_traits)

    if g.user_session.logged_in:
        uc = model.UserCollection()
        uc.name = collection_name
        print("user_session:", g.user_session.__dict__)
        uc.user = g.user_session.user_id
        uc.members = json.dumps(list(traits))
        db_session.add(uc)
        db_session.commit()
        return redirect(url_for('view_collection', uc_id=uc.id))
    else:
        current_collections = user_manager.AnonUser().get_collections()
        ac = AnonCollection(collection_name)
        ac.changed_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        ac.add_traits(params)
        return redirect(url_for('view_collection', collection_id=ac.id))

@app.route("/collections/list")
def list_collections():
    params = request.args
    print("PARAMS:", params)
    if g.user_session.logged_in:
        user_collections = list(g.user_session.user_ob.user_collections)
        print("user_collections are:", user_collections)
        return render_template("collections/list.html",
                               params = params,
                               collections = user_collections,
                               )
    else:
        anon_collections = user_manager.AnonUser().get_collections()
        print("anon_collections are:", anon_collections)
        return render_template("collections/list.html",
                               params = params,
                               collections = anon_collections)


@app.route("/collections/remove", methods=('POST',))
def remove_traits():
    params = request.form
    print("params are:", params)

    if "uc_id" in params:
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        traits_to_remove = params.getlist('traits[]')
        traits_to_remove = process_traits(traits_to_remove)
        print("\n\n  after processing, traits_to_remove:", traits_to_remove)
        all_traits = uc.members_as_set()
        members_now = all_traits - traits_to_remove
        print("  members_now:", members_now)
        uc.members = json.dumps(list(members_now))
        uc.changed_timestamp = datetime.datetime.utcnow()
        db_session.commit()
    else:
        collection_name = params['collection_name']
        members_now = AnonCollection(collection_name).remove_traits(params)


    # We need to return something so we'll return this...maybe in the future
    # we can use it to check the results
    return str(len(members_now))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    params = request.form
    print("params:", params)
    if g.user_session.logged_in:
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        # Todo: For now having the id is good enough since it's so unique
        # But might want to check ownership in the future
        collection_name = uc.name
        db_session.delete(uc)
        db_session.commit()
    else:
        collection_name = params['collection_name']
        user_manager.AnonUser().delete_collection(collection_name)

    flash("We've deleted the collection: {}.".format(collection_name), "alert-info")

    return redirect(url_for('list_collections'))


@app.route("/collections/view")
def view_collection():
    params = request.args
    print("PARAMS in view collection:", params)

    if "uc_id" in params:
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        traits = json.loads(uc.members)
    else:
        user_collections = json.loads(Redis.get(user_manager.AnonUser().key))
        this_collection = {}
        for collection in user_collections:
            if collection['id'] == params['collection_id']:
                this_collection = collection
                break
        #this_collection = user_collections[params['collection_id']]
        traits = this_collection['members']

    print("in view_collection traits are:", traits)

    trait_obs = []
    json_version = []

    for atrait in traits:
        name, dataset_name = atrait.split(':')

        trait_ob = trait.GeneralTrait(name=name, dataset_name=dataset_name)
        trait_ob.retrieve_info(get_qtl_info=True)
        trait_obs.append(trait_ob)

        json_version.append(trait_ob.jsonable())

    if "uc_id" in params:
        collection_info = dict(trait_obs=trait_obs,
                               uc = uc)
    else:
        collection_info = dict(trait_obs=trait_obs,
                               collection_name=this_collection['name'])
    if "json" in params:
        print("json_version:", json_version)
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html",
                           **collection_info
                           )
