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




@app.route("/collections/add")
def collections_add():
    user_collections = g.user_session.user_ob.user_collections
    print("user_collections are:", user_collections)
    return render_template("collections/add.html",
                           traits=request.args['traits'],
                           user_collections = user_collections,
                           )


@app.route("/collections/new")
def collections_new():
    params = request.args
    print("request.args in collections_new are:", params)

    collection_name = params['new_collection']

    if "create_new" in params:
        return create_new(collection_name)
    elif "add_to_existing" in params:
        return add_traits(params, collection_name)
    elif "default" in params:
        return add_traits(params, "default")

    else:
        CauseAnError



def add_traits(params, collection_name):
    print("---> params are:", params.keys())
    print("     type(params):", type(params))
    if collection_name=="default":
        uc = g.user_session.user_ob.get_collection_by_name("default")
        # Doesn't exist so we'll create it
        if not uc:
            return create_new("default")
    else:
        uc = model.UserCollection.query.get(params['existing_collection'])
    members = set(json.loads(uc.members))
    len_before = len(members)

    traits = process_traits(params['traits'])

    members_now = list(members | traits)
    len_now = len(members_now)
    uc.members = json.dumps(members_now)

    uc.changed_timestamp = datetime.datetime.utcnow()

    db_session.commit()

    print("added to existing, now set is:" + str(uc.members))

    new_length = len_now - len_before
    if new_length:
        flash("We've added {} to your collection.".format(
            numify(new_length, 'new trait', 'new traits')))
    else:
        flash("No new traits were added.")

    return redirect(url_for('view_collection', uc_id=uc.id))

def process_traits(unprocessed_traits):
    print("unprocessed_traits are:", unprocessed_traits)
    unprocessed_traits = unprocessed_traits.split(",")
    traits = set()
    for trait in unprocessed_traits:
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
    user_collections = g.user_session.user_ob.user_collections
    return render_template("collections/list.html",
                           params = params,
                           user_collections = user_collections,
                           )


@app.route("/collections/view")
def view_collection():
    params = request.args
    print("params in view collection:", params)
    uc_id = params['uc_id']
    uc = model.UserCollection.query.get(uc_id)
    traits = json.loads(uc.members)

    print("in view_collection traits are:", traits)

    trait_obs = []
    json_version = []

    for atrait in traits:
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
                           uc =     uc)
    if "json" in params:
        print("json_version:", json_version)
        return json.dumps(json_version)
    else:
        return render_template("collections/view.html",
                           **collection_info
                           )
