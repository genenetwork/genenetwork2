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
                   redirect, flash, jsonify, session)

from wqflask import app

from pprint import pformat as pf

from wqflask.database import db_session

from wqflask import model
from wqflask import user_manager
from wqflask.user_manager import AnonUser

from utility import Bunch, Struct
from utility.formatting import numify

from base import trait
from base.data_set import create_dataset

import logging
from utility.logger import getLogger
logger = getLogger(__name__)

from .util_functions import (get_collections_by_user_key, process_traits,
                             save_collection, delete_collection_by_id,add_traits,
                             get_collection_by_id, get_timestamp_string,
                             remove_traits, num_members, get_anon_collection,
                             get_members)

def report_change(len_before, len_now):
    new_length = len_now - len_before
    if new_length:
        logger.debug("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
    else:
        logger.debug("No new traits were added.")


@app.route("/collections/add")
def collections_add():
    traits=request.args['traits']

    if session.get("user", None):
        logger.debug("user_session",g.user_session)
        user_collections = get_collections_by_user_key(session["user"]["user_id"])
        logger.debug("user_collections are:", user_collections)
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
        logger.debug("in create_new")
        collection_name = params['new_collection']
        return create_new(collection_name)
    elif "add_to_existing" in params:
        logger.debug("in add to existing")
        collection_name = params['existing_collection'].split(":")[1]
        if session.get("user", None):
            collection_id = params["existing_collection"].split(":")[0]
            traits = process_traits(params["traits"])
            collection = add_traits(
                get_collection_by_id(collection_id=collection_id), traits)
            save_collection(collection_id, collection)
            return redirect(url_for('view_collection', uc_id=collection_id))
        else:
            ac = add_traits(get_anon_collection(collection_name, AnonUser()),
                            process_traits(params["traits"]))
            save_collection(ac["id"], ac)
            return redirect(url_for('view_collection', collection_id=ac["id"]))
    else:
        CauseAnError

def create_new(collection_name):
    params = request.args

    unprocessed_traits = params['traits']
    traits = process_traits(unprocessed_traits)

    if session.get("user", None):
        collection_id = str(uuid.uuid4())
        created_timestamp = get_timestamp_string()
        collection = {
            "id": collection_id,
            "name": collection_name,
            "user_key": session["user"]["user_id"],
            "created_timestamp": created_timestamp,
            "changed_timestamp": created_timestamp,
            "members": list(traits),
            "num_members": len(traits)
        }
        save_collection(collection_id=collection_id, collection=collection)
        return redirect(url_for('view_collection', uc_id=collection_id))
    else:
        ac = add_traits(get_anon_collection(collection_name, AnonUser()),
                        process_traits(params["traits"]))
        save_collection(collection_id=ac["id"], collection=ac)
        return redirect(url_for('view_collection', collection_id=ac["id"]))

@app.route("/collections/list")
def list_collections():
    params = request.args
    logger.debug("PARAMS:", params)
    if session.get("user", None):
        collections = get_collections_by_user_key(session["user"]["user_id"])
        logger.debug("user_collections are:", collections)
    else:
        collections = get_collections_by_user_key(user_manager.AnonUser().key)
        logger.debug("anon_collections are:", collections)

    return render_template("collections/list.html",
                           params = params,
                           collections = collections,
                           datetime = datetime.datetime,
                           num_collections=len(collections))


@app.route("/collections/remove", methods=('POST',))
def remove_collection_traits():
    params = request.form
    logger.debug("params are:", params)
    traits = process_traits(params.getlist('traits[]'))

    if "uc_id" in params:
        collection = remove_traits(get_collection_by_id(params['uc_id']), traits)
    else:
        collection = remove_traits(
            get_anon_collection(params['collection_name'], AnonUser()), traits)


    # We need to return something so we'll return this...maybe in the future
    # we can use it to check the results
    save_collection(collection["id"], collection)
    return str(num_members(collection))


@app.route("/collections/delete", methods=('POST',))
def delete_collection():
    params = request.form
    logger.debug("params:", params)
    colls = []
    if session.get("user", None):
        uc_id = params['uc_id']
        if len(uc_id.split(":")) > 1:
            for this_uc_id in uc_id.split(":"):
                coll = get_collection_by_id(collection_id = this_uc_id)
                delete_collection_by_id(collection_id = this_uc_id)
                colls.append(coll["name"])
            collection_name = ", ".join(colls)
        else:
            coll = get_collection_by_id(collection_id = uc_id)
            delete_collection_by_id(collection_id = uc_id)
            collection_name = coll["name"]
    else:
        if "collection_name" in params:
            collection_name = params['collection_name']
        else:
            for this_collection in params['uc_id'].split(":"):
                user_manager.AnonUser().delete_collection(this_collection)
                colls.append(this_collection)
            collection_name = ", ".join(colls)

    flash("We've deleted the collection(s): {}.".format(collection_name), "alert-info")

    return redirect(url_for('list_collections'))


@app.route("/collections/view")
def view_collection():
    params = request.args
    logger.debug("PARAMS in view collection:", params)

    this_collection = get_collection_by_id(params['collection_id'])
    traits = this_collection.get('members', [])
    logger.debug("in view_collection traits are:", traits)

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

    collection_info = dict(trait_obs=trait_obs,
                           uc = this_collection,
                           collection_name=this_collection['name'])

    if "json" in params:
        logger.debug("json_version:", json_version)
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html", **collection_info)
