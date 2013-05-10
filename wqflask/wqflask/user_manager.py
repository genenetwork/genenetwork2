from __future__ import print_function, division, absolute_import

"""Access things in template like this:

    x: {{ g.identity.name }}
    security: {{ security.__dict__ }}

"""

from wqflask import model

from flask import Flask, g

#from app import db
print("globals are:", globals())


class UserManager(object):
    def __init__(self):
        self.users = model.User.query.all()
        print("Users are:", self.users)

