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
                   redirect, flash)

from wqflask import app


from pprint import pformat as pf


from wqflask.database import db_session

from wqflask import model

from utility import Bunch, Struct

from wqflask import user_manager






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
    print("request.args in collections_new are:", request.args)
    if "create_new" in request.args:
        return create_new()
    elif "add_to_existing" in request.args:
        return add_to_existing()
    elif "continue" in request.args:
        return unnamed()
    else:
        CauseAnError


def unnamed():
    return "unnamed"

def add_to_existing():
    params = request.args
    print("---> params are:", params.keys())
    print("     type(params):", type(params))
    uc = model.UserCollection.query.get(params['existing_collection'])
    members = set(json.loads(uc.members))

    traits = process_traits(params['traits'])

    uc.members = json.dumps(list(members | traits))

    uc.changed_timestamp = datetime.datetime.utcnow()

    db_session.commit()

    return "added to existing, now set is:" + str(uc.members)

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

def create_new():
    params = request.args
    uc = model.UserCollection()
    uc.name = params['new_collection']
    print("user_session:", g.user_session.__dict__)
    uc.user = g.user_session.user_id
    unprocessed_traits = params['traits']

    traits = process_traits(unprocessed_traits)

    uc.members = json.dumps(list(traits))
    print("traits are:", traits)

    db_session.add(uc)
    db_session.commit()

    return "Created: " + uc.name
