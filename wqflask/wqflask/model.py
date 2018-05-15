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

from wqflask.database import Base, init_db



# Define models
#roles_users = Table('roles_users',
#        Column('user_id', Integer(), ForeignKey('user.the_id')),
#        Column('role_id', Integer(), ForeignKey('role.the_id')))

#class Role(Base):
#    __tablename__ = "role"
#    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
#    name = Column(Unicode(80), unique=True, nullable=False)
#    description = Column(Unicode(255))


    #roles = relationship('Role', secondary=roles_users,
    #                        backref=backref('users', lazy='dynamic'))

##################################################################################################

class UserCollection(Base):
    __tablename__ = "user_collection"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))

    # I'd prefer this to not have a length, but for the index below it needs one
    name = Column(Unicode(50))
    created_timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    changed_timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    members = Column(Text)  # We're going to store them as a json list

    # This index ensures a user doesn't have more than one collection with the same name
    __table_args__ = (Index('usercollection_index', "user", "name"), )

    @property
    def num_members(self):
        try:
            return len(json.loads(self.members))
        except:
            return 0

    #@property
    #def display_num_members(self):
    #    return display_collapsible(self.num_members)

    def members_as_set(self):
        return set(json.loads(self.members))


def display_collapsible(number):
    if number:
        return number
    else:
        return ""


def user_uuid():
    """Unique cookie for a user"""
    user_uuid = request.cookies.get('user_uuid')

