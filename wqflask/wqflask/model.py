from __future__ import print_function, division, absolute_import

import uuid
import datetime

import simplejson as json

from flask import request
from flask.ext.sqlalchemy import SQLAlchemy

from wqflask import app

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Unicode, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, backref

from wqflask.database import Base, init_db



# Define models
#roles_users = Table('roles_users',
#        Column('user_id', Integer(), ForeignKey('user.the_id')),
#        Column('role_id', Integer(), ForeignKey('role.the_id')))

class Role(Base):
    __tablename__ = "role"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    name = Column(Unicode(80), unique=True, nullable=False)
    description = Column(Unicode(255))

class User(Base):
    __tablename__ = "user"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    email_address = Column(Unicode(50), unique=True, nullable=False)

    # Todo: Turn on strict mode for Mysql
    password = Column(Text, nullable=False)

    full_name = Column(Unicode(50))
    organization = Column(Unicode(50))

    active = Column(Boolean(), nullable=False, default=True)

    registration_info = Column(Text)   # json detailing when they were registered, etc.

    confirmed = Column(Text) # json detailing when they confirmed, etc.

    logins = relationship("Login",
                          order_by="desc(Login.timestamp)",
                          lazy='dynamic' # Necessary for filter in login_count
                          )

    user_collections = relationship("UserCollection",
                          order_by="asc(UserCollection.name)",
                          )

    @property
    def login_count(self):
        return self.logins.filter_by(successful=True).count()


    @property
    def confirmed_at(self):
        if self.confirmed:
            confirmed_info = json.loads(self.confirmed)
            return confirmed_info['timestamp']
        else:
            return None

    @property
    def most_recent_login(self):
        try:
            return self.logins[0]
        except IndexError:
            return None


    #roles = relationship('Role', secondary=roles_users,
    #                        backref=backref('users', lazy='dynamic'))


class Login(Base):
    __tablename__ = "login"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))
    timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    ip_address = Column(Unicode(39))
    successful = Column(Boolean(), nullable=False)  # False if wrong password was entered
    session_id = Column(Text)  # Set only if successfully logged in, otherwise should be blank

    def __init__(self, user):
        self.user = user.id
        self.ip_address = request.remote_addr

##################################################################################################

class UserCollection(Base):
    __tablename__ = "user_collection"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))
    name = Column(Text)
    created_timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    changed_timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    members = Column(Text)  # We're going to store them as a json list

    # This index ensures a user doesn't have more than one collection with the same name
    __table_args__ = (Index('usercollection_index', "user", "name"), )
