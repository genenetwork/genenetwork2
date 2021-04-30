import uuid
import datetime

import simplejson as json

from flask import request

from wqflask import app

import sqlalchemy
from sqlalchemy import (Column, ForeignKey, Unicode, Boolean, DateTime,
                        Text, Index)
from sqlalchemy.orm import relationship

from wqflask.database import Base, init_db


class User(Base):
    __tablename__ = "user"
    id = Column(Unicode(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    email_address = Column(Unicode(50), unique=True, nullable=False)

    # Todo: Turn on strict mode for Mysql
    password = Column(Text, nullable=False)

    full_name = Column(Unicode(50))
    organization = Column(Unicode(50))

    active = Column(Boolean(), nullable=False, default=True)

    # json detailing when they were registered, etc.
    registration_info = Column(Text)

    confirmed = Column(Text)  # json detailing when they confirmed, etc.

    # json detailing when they became a superuser, otherwise empty
    superuser = Column(Text)
                       # if not superuser

    logins = relationship("Login",
                          order_by="desc(Login.timestamp)",
                          lazy='dynamic',  # Necessary for filter in login_count
                          foreign_keys="Login.user",
                          )

    user_collections = relationship("UserCollection",
                          order_by="asc(UserCollection.name)",
                          lazy='dynamic',
                          )

    def display_num_collections(self):
        """
        Returns the number of collections or a blank string if there are zero.


        Because this is so unimportant...we wrap the whole thing in a try/expect...last thing we
        want is a webpage not to be displayed because of an error here

        Importand TODO: use redis to cache this, don't want to be constantly computing it

        """
        try:
            num = len(list(self.user_collections))
            return display_collapsible(num)
        except Exception as why:
            print("Couldn't display_num_collections:", why)
            return ""

    def get_collection_by_name(self, collection_name):
        try:
            collect = self.user_collections.filter_by(
                name=collection_name).first()
        except sqlalchemy.orm.exc.NoResultFound:
            collect = None
        return collect

    @property
    def name_and_org(self):
        """Nice shortcut for printing out who the user is"""
        if self.organization:
            return "{} from {}".format(self.full_name, self.organization)
        else:
            return self.full_name

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
    def superuser_info(self):
        if self.superuser:
            return json.loads(self.superuser)
        else:
            return None

    @property
    def crowner(self):
        """If made superuser, returns object of person who did the crowning"""
        if self.superuser:
            superuser_info = json.loads(self.superuser)
            crowner = User.query.get(superuser_info['crowned_by'])
            return crowner
        else:
            return None

    @property
    def most_recent_login(self):
        try:
            return self.logins[0]
        except IndexError:
            return None


class Login(Base):
    __tablename__ = "login"
    id = Column(Unicode(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))
    timestamp = Column(DateTime(), default=lambda: datetime.datetime.utcnow())
    ip_address = Column(Unicode(39))
    # False if wrong password was entered
    successful = Column(Boolean(), nullable=False)
    # Set only if successfully logged in, otherwise should be blank
    session_id = Column(Text)

    # Set to user who assumes identity if this was a login for debugging purposes by a superuser
    assumed_by = Column(Unicode(36), ForeignKey('user.id'))

    def __init__(self, user):
        self.user = user.id
        self.ip_address = request.remote_addr

##################################################################################################


class UserCollection(Base):
    __tablename__ = "user_collection"
    id = Column(Unicode(36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))

    # I'd prefer this to not have a length, but for the index below it needs one
    name = Column(Unicode(50))
    created_timestamp = Column(
        DateTime(), default=lambda: datetime.datetime.utcnow())
    changed_timestamp = Column(
        DateTime(), default=lambda: datetime.datetime.utcnow())
    members = Column(Text)  # We're going to store them as a json list

    # This index ensures a user doesn't have more than one collection with the same name
    __table_args__ = (Index('usercollection_index', "user", "name"), )

    @property
    def num_members(self):
        try:
            return len(json.loads(self.members))
        except:
            return 0

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
