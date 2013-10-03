from __future__ import print_function, division, absolute_import

import uuid

from flask.ext.sqlalchemy import SQLAlchemy
#from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin

#from flask_security.forms import TextField
#from flask_security.forms import RegisterForm

from wqflask import app

from sqlalchemy import Column, Integer, String, Table, ForeignKey, Unicode, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, backref

from wqflask.database import Base, init_db

# Create database connection object
#db = SQLAlchemy(app)


# Is this right? -Sam
#from sqlalchemy.ext.declarative import declarative_base
#Base = declarative_base()

#@classmethod
#def get(cls, key):
#    """Convenience get method using the primary key
#
#    If record doesn't exist, returns None
#
#    Allows the following:  User.get('121')
#
#    """
#    print("in get cls is:", cls)
#    print("  key is {} : {}".format(type(key), key))
#    query = Model.query(cls)
#    print("query is: ", query)
#    record = query.get(key)
#    return record
#
#
#print("Model is:", vars(Model))
#Model.get = get

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

    #last_login_at = Column(DateTime())
    #current_login_at = Column(DateTime())
    #last_login_ip = Column(Unicode(39))
    #current_login_ip = Column(Unicode(39))
    #login_count = Column(Integer())

    #roles = relationship('Role', secondary=roles_users,
    #                        backref=backref('users', lazy='dynamic'))

class Login(Base):
    __tablename__ = "login"
    id = Column(Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    user = Column(Unicode(36), ForeignKey('user.id'))
    timestamp = Column(DateTime())
    ip_address = Column(Unicode(39))

# Setup Flask-Security
#user_datastore = SQLAlchemyUserDatastore(db, User, Role)

#class ExtendedRegisterForm(RegisterForm):
#    name = TextField('name')
#    #print("name is:", name['_name'], vars(name))
#    organization = TextField('organization')
#
#security = Security(app, user_datastore, register_form=ExtendedRegisterForm)


#user_datastore.create_role(name="Genentech", description="Genentech Beta Project(testing)")


