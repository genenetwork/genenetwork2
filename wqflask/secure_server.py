from __future__ import print_function, division, absolute_import

from wqflask import app

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
     UserMixin, RoleMixin

# Create app
#app = Flask(__name__)
app.config['SECRET_KEY'] = 'LjfrbDOlvdFMT5cCi9qrJqStxK4NcmxW'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://webqtl:f2ZypIflRM@gn.cazhbciu2y1i.us-east-1.rds.amazonaws.com/db_webqtl'
#app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_TRACKABLE'] = True

# Create database connection object
db = SQLAlchemy(app)

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
    last_login_ip_= db.Column(db.String(39))
    current_login_ip = db.Column(db.String(39))
    login_count = db.Column(db.Integer())
    
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
#@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(email='matt@example.com', password='notebook')
    db.session.commit()

## Views
#@app.route('/')
#def home():
#    return render_template('index.html')

import logging
#from themodule import TheHandlerYouWant
file_handler = logging.FileHandler("/tmp/flask_gn_log")
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

import logging_tree
logging_tree.printout()

if __name__ == '__main__':
    #create_user()
    app.run(host='0.0.0.0',
        use_debugger=False,
        threaded=True,
        use_reloader=True)
