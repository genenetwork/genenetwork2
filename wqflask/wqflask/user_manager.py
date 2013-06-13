from __future__ import print_function, division, absolute_import

"""Access things in template like this:

    x: {{ g.identity.name }}
    security: {{ security.__dict__ }}

"""

from wqflask import model

from flask import Flask, g

from pprint import pformat as pf

#from app import db
print("globals are:", globals())


class UsersManager(object):
    def __init__(self):
        self.users = model.User.query.all()
        print("Users are:", self.users)



class UserManager(object):
    def __init__(self, kw):
        self.user_id = int(kw['user_id'])
        print("In UserManager locals are:", pf(locals()))
        #self.user = model.User.get(user_id)
        #print("user is:", user)
        self.user = model.User.query.get(self.user_id)
        print("user is:", self.user)


class RolesManager(object):
    def __init__(self):
        self.roles = model.Role.query.all()
        print("Roles are:", self.roles)
