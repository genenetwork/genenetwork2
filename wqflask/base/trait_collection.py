#The TraitCollection class with encompass the UserCollection (collections
#created by registered and logged in users) and AnonCollection (collections created by users who
#aren't logged in) class. The former will represent and act on a database table while the latter
#will store its trait information in Redis


from __future__ import print_function, division, absolute_import

import uuid
import datetime

import simplejson as json

from flask import request
from flask.ext.sqlalchemy import SQLAlchemy

from wqflask import app

import sqlalchemy

from sqlalchemy import (Column, Integer, String, Table, ForeignKey, Unicode, Boolean, DateTime,
                        Text, Index)
from sqlalchemy.orm import relationship, backref

#from redis import StrictRedis
import redis
Redis = redis.StrictRedis()

from wqflask.database import Base, init_db

class TraitCollection(object):


class AnonCollection(TraitCollection):
    
    def __init__(self, anon_id)
        self.anon_id = anon_id
        self.collection_members = Redis.smembers(self.anon_id)
        print("self.collection_members is:", self.collection_members)
        self.num_members = len(self.collection_members)
        

    @app.route("/collections/remove", methods=('POST',))
    def remove_traits(traits_to_remove):
        print("traits_to_remove:", traits_to_remove)
        for trait in traits_to_remove:
            Redis.srem(self.anon_id, trait)
        members_now = self.collection_members - traits_to_remove
        print("members_now:", members_now)
        print("Went from {} to {} members in set.".format(len(self.collection_members), len(members_now)))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len(members_now))

    @property
    def num_members(self):
        print("members are:", json.loads(self.members))
        return len(json.loads(self.members))

    #@property
    #def display_num_members(self):
    #    return display_collapsible(self.num_members)

    def members_as_set(self):
        return set(json.loads(self.members))