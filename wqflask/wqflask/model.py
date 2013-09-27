from __future__ import print_function, division, absolute_import

import uuid

from flask.ext.sqlalchemy import SQLAlchemy
#from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin

#from flask_security.forms import TextField
#from flask_security.forms import RegisterForm

from wqflask import app

# Create database connection object
db = SQLAlchemy(app)

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
#    query = db.Model.query(cls)
#    print("query is: ", query)
#    record = query.get(key)
#    return record
#
#
#print("db.Model is:", vars(db.Model))
#db.Model.get = get

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.the_id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.the_id')))

class Role(db.Model):
    the_id = db.Column(db.Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    name = db.Column(db.Unicode(80), unique=True, nullable=False)
    description = db.Column(db.Unicode(255))

class User(db.Model):
    the_id = db.Column(db.Unicode(36), primary_key=True, default=lambda: unicode(uuid.uuid4()))
    email_address = db.Column(db.Unicode(50), unique=True, nullable=False)
    
    password = db.Column(db.Unicode(24), nullable=False)
    salt = db.Column(db.Unicode(32), nullable=False)
    password_info = db.Column(db.Unicode(50))
    
    full_name = db.Column(db.Unicode(50))
    organization = db.Column(db.Unicode(50))
    
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.Unicode(39))
    current_login_ip = db.Column(db.Unicode(39))
    login_count = db.Column(db.Integer())

    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
#user_datastore = SQLAlchemyUserDatastore(db, User, Role)

#class ExtendedRegisterForm(RegisterForm):
#    name = TextField('name')
#    #print("name is:", name['_name'], vars(name))
#    organization = TextField('organization')
#
#security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

db.metadata.create_all(db.engine)

#user_datastore.create_role(name="Genentech", description="Genentech Beta Project(testing)")
