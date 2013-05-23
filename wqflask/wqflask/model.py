from __future__ import print_function, division, absolute_import

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin

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
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())

    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(39))
    current_login_ip = db.Column(db.String(39))
    login_count = db.Column(db.Integer())

    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

db.metadata.create_all(db.engine)



