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

from wqflask.database import Base, init_db

class TraitCollection(object):
