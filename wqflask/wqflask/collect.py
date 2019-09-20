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
from base.data_set import create_dataset

import logging
from utility.logger import getLogger
logger = getLogger(__name__)


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

    def add_traits(self, unprocessed_traits):
        #assert collection_name == "Default", "Unexpected collection name for anonymous user"
        self.traits = list(process_traits(unprocessed_traits))
        existing_collections = Redis.get(self.key)
        logger.debug("existing_collections:", existing_collections)
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
        Redis.set(self.key, json.dumps(collections_list))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len_now)

def process_traits(unprocessed_traits):
    if isinstance(unprocessed_traits, basestring):
        unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
        #print("trait is:", trait)
        data, _separator, hmac = trait.rpartition(':')
        data = data.strip()
        if g.user_session.logged_in:
          assert hmac==user_manager.actual_hmac_creation(data), "Data tampering?"
        traits.add(str(data))

    return traits

def report_change(len_before, len_now):
    new_length = len_now - len_before
    if new_length:
        logger.debug("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
    else:
        logger.debug("No new traits were added.")

@app.route("/collections/store_trait_list", methods=('POST',))
def store_traits_list():
   params = request.form

   traits = params['traits']
   hash = params['hash']

   Redis.set(hash, traits)

   return hash

@app.route("/collections/add")
def collections_add():
    if g.user_session.logged_in:
        collections = g.user_session.user_collections
        if len(collections) < 1:
            collection_name = "Default Collection"
            uc_id = g.user_session.add_collection(collection_name, set())
            collections = g.user_session.user_collections
    else:
        anon_collections = user_manager.AnonUser().get_collections()
        collections = []
        for collection in anon_collections:
            collections.append({'id':collection['id'], 'name':collection['name']})

    if 'traits' in request.args:
        traits=request.args['traits']
        return render_template("collections/add.html",
                                traits = traits,
                                collections = collections,
                              )
    else:
        hash = request.args['hash']
        return render_template("collections/add.html",
                                hash = hash,
                                collections = collections,
                              )

@app.route("/collections/new")
def collections_new():
    params = request.args

    if "sign_in" in params:
        return redirect(url_for('login'))
    if "create_new" in params:
        logger.debug("in create_new")
        collection_name = params['new_collection']
        if collection_name.strip() == "":
            collection_name = datetime.datetime.utcnow().strftime('Collection_%b_%d_%H:%M')
        return create_new(collection_name)
    elif "add_to_existing" in params:
        logger.debug("in add to existing")
        if 'existing_collection' not in params:
            default_collection_exists = False
            if g.user_session.logged_in:
                collections = g.user_session.user_collections
            else:
                collections = user_manager.AnonUser().get_collections()
            for collection in collections:
                if collection["name"] == "Default Collection":
                    collection_id = collection["id"]
                    collection_name = collection["name"]
                    default_collection_exists = True
            if not default_collection_exists:
                return create_new("Default Collection")
        else:
            collection_id = params['existing_collection'].split(":")[0]
            collection_name = params['existing_collection'].split(":")[1]
        if g.user_session.logged_in:
            if "hash" in params:
                unprocessed_traits = Redis.get(params['hash'])
            else:
                unprocessed_traits = params['traits']
            traits = list(process_traits(unprocessed_traits))
            g.user_session.add_traits_to_collection(collection_id, traits)
            return redirect(url_for('view_collection', uc_id=collection_id))
        else:
            ac = AnonCollection(collection_name)
            if "hash" in params:
                unprocessed_traits = Redis.get(params['hash'])
            else:
                unprocessed_traits = params['traits']
            ac.add_traits(unprocessed_traits)
            return redirect(url_for('view_collection', collection_id=ac.id))
    else:
        CauseAnError

def create_new(collection_name):
    params = request.args

    if "hash" in params:
        unprocessed_traits = Redis.get(params['hash'])
        Redis.delete(hash)
    else:
        unprocessed_traits = params['traits']

    traits = process_traits(unprocessed_traits)

    if g.user_session.logged_in:
        uc_id = g.user_session.add_collection(collection_name, traits)

        return redirect(url_for('view_collection', uc_id=uc_id))
    else:
        ac = AnonCollection(collection_name)
        ac.changed_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        ac.add_traits(unprocessed_traits)
        return redirect(url_for('view_collection', collection_id=ac.id))

@app.route("/collections/list")
def list_collections():
    params = request.args

    if g.user_session.logged_in:
        user_collections = list(g.user_session.user_collections)
        #logger.debug("user_collections are:", user_collections)
        return render_template("collections/list.html",
                               params = params,
                               collections = user_collections,
                               )
    else:
        anon_collections = user_manager.AnonUser().get_collections()
        #logger.debug("anon_collections are:", anon_collections)
        return render_template("collections/list.html",
                               params = params,
                               collections = anon_collections)


@app.route("/collections/remove", methods=('POST',))
def remove_traits():
    params = request.form

    if "uc_id" in params:
        uc_id = params['uc_id']
        traits_to_remove = params.getlist('traits[]')
        traits_to_remove = process_traits(traits_to_remove)
        logger.debug("\n\n  after processing, traits_to_remove:", traits_to_remove)

        members_now = g.user_session.remove_traits_from_collection(uc_id, traits_to_remove)
    else:
        collection_name = params['collection_name']
        members_now = AnonCollection(collection_name).remove_traits(params)


    # We need to return something so we'll return this...maybe in the future
    # we can use it to check the results
    return str(len(members_now))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    params = request.form
    uc_id = ""
    if g.user_session.logged_in:
        uc_id = params['uc_id']
        if len(uc_id.split(":")) > 1:
            for this_uc_id in uc_id.split(":"):
                collection_name = g.user_session.delete_collection(this_uc_id)
        else:
            collection_name = g.user_session.delete_collection(uc_id)
    else:
        if "collection_name" in params:
            collection_name = params['collection_name']
            user_manager.AnonUser().delete_collection(collection_name)
        else:
            uc_id = params['uc_id']
            for this_collection in uc_id.split(":"):
                user_manager.AnonUser().delete_collection(this_collection)

    if uc_id != "":
        if len(uc_id.split(":")) > 1:
            flash("We've deleted the selected collections.", "alert-info")
        else:
            flash("We've deleted the collection: {}.".format(uc_id), "alert-info")
    else:
        flash("We've deleted the collection: {}.".format(collection_name), "alert-info")

    return redirect(url_for('list_collections'))


@app.route("/collections/view")
def view_collection():
    params = request.args

    if g.user_session.logged_in and "uc_id" in params:
        uc_id = params['uc_id']
        uc = (collection for collection in g.user_session.user_collections if collection["id"] == uc_id).next()
        traits = uc["members"]
    else:
        user_collections = json.loads(Redis.get(user_manager.AnonUser().key))
        this_collection = {}
        for collection in user_collections:
            if collection['id'] == params['collection_id']:
                this_collection = collection
                break

        traits = this_collection['members']

    trait_obs = []
    json_version = []

    for atrait in traits:
        name, dataset_name = atrait.split(':')
        if dataset_name == "Temp":
            group = name.split("_")[2]
            dataset = create_dataset(dataset_name, dataset_type = "Temp", group_name = group)
            trait_ob = trait.GeneralTrait(name=name, dataset=dataset)
        else:
            dataset = create_dataset(dataset_name)
            trait_ob = trait.GeneralTrait(name=name, dataset=dataset)
            trait_ob = trait.retrieve_trait_info(trait_ob, dataset, get_qtl_info=True)
        trait_obs.append(trait_ob)

        json_version.append(trait.jsonable(trait_ob))

    if "uc_id" in params:
        collection_info = dict(trait_obs=trait_obs,
                               uc = uc)
    else:
        collection_info = dict(trait_obs=trait_obs,
                               collection_name=this_collection['name'])
    if "json" in params:
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html",
                           **collection_info
                           )