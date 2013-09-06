from __future__ import print_function, division, absolute_import

"""Access things in template like this:

    x: {{ g.identity.name }}
    security: {{ security.__dict__ }}

"""

from wqflask import model

from utility import Bunch

from flask import Flask, g

from pprint import pformat as pf

from base.data_set import create_datasets_list

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
        datasets = create_datasets_list()
        for dataset in datasets:
            if not dataset.check_confidentiality():
                continue
            print("\n  Name:", dataset.name)
            print("  Type:", dataset.type)
            print("  ID:", dataset.id)
            print("  Confidential:", dataset.check_confidentiality())
        #print("   ---> self.datasets:", self.datasets)
        

class RegisterUser(object):
    def __init__(self, kw):
        self.errors = []
        user = Bunch()
        
        user.email_address = kw.get('email_address', '').strip()
        if not (5 <= len(user.email_address) <= 50):
            self.errors.append('Email Address needs to be between 5 and 50 characters.')
            
        user.full_name = kw.get('full_name', '').strip()
        if not (5 <= len(user.full_name) <= 50):
            self.errors.append('Full Name needs to be between 5 and 50 characters.')
            
        user.organization = kw.get('organization', '').strip()
        if user.organization and not (5 <= len(user.organization) <= 50):
            self.errors.append('Organization needs to be empty or between 5 and 50 characters.')

        user.password = kw.get('password', '')
        if not (6 <= len(user.password) <= 30):
            self.errors.append('Password needs to be between 6 and 30 characters.')
            
        if kw.get('password_confirm') != user.password:
            self.errors.append("Passwords don't match.")
        
        if self.errors:
            return 
        
    



class GroupsManager(object):
    def __init__(self, kw):
        self.datasets = create_datasets_list()


class RolesManager(object):
    def __init__(self):
        self.roles = model.Role.query.all()
        print("Roles are:", self.roles)
