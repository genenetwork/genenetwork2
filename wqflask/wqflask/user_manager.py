from __future__ import print_function, division, absolute_import

"""Access things in template like this:

    x: {{ g.identity.name }}
    security: {{ security.__dict__ }}

"""

import os
import hashlib
import datetime
import time

import simplejson as json

from wqflask import pbkdf2

from wqflask.database import db_session

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
        self.user = Bunch()
        
        self.user.email_address = kw.get('email_address', '').strip()
        if not (5 <= len(self.user.email_address) <= 50):
            self.errors.append('Email Address needs to be between 5 and 50 characters.')
            
        self.user.full_name = kw.get('full_name', '').strip()
        if not (5 <= len(self.user.full_name) <= 50):
            self.errors.append('Full Name needs to be between 5 and 50 characters.')
            
        self.user.organization = kw.get('organization', '').strip()
        if self.user.organization and not (5 <= len(self.user.organization) <= 50):
            self.errors.append('Organization needs to be empty or between 5 and 50 characters.')

        password = str(kw.get('password', ''))
        if not (6 <= len(password)):
            self.errors.append('Password needs to be at least 6 characters.')
            
        if kw.get('password_confirm') != password:
            self.errors.append("Passwords don't match.")
        
        if self.errors:
            return
        
        print("No errors!")
        
        self.set_password(password)
        
        new_user = model.User(**self.user.__dict__)
        db_session.add(new_user)
        db_session.commit()
        
    
    def set_password(self, password):
        pwfields = Bunch()
        algo_string = "sha256"
        algorithm = getattr(hashlib, algo_string)
        pwfields.algorithm = "pbkdf2-" + algo_string
        pwfields.salt = os.urandom(32)

        # https://forums.lastpass.com/viewtopic.php?t=84104
        pwfields.iterations = 100000   
        pwfields.keylength = 24
        
        pwfields.created_ts = datetime.datetime.utcnow().isoformat()
        # One more check on password length
        assert len(password) >= 6, "Password shouldn't be so short here"
        
        print("pwfields:", vars(pwfields))
        print("locals:", locals())
        start_time = time.time()
        pwfields.password = pbkdf2.pbkdf2_hex(password, pwfields.salt, pwfields.iterations, pwfields.keylength, algorithm)
        print("Creating password took:", time.time() - start_time)
        self.user.password = json.dumps(pwfields.__dict__,
                                        sort_keys=True,
                                        # See http://stackoverflow.com/a/12312896
                                        encoding="latin-1"
                                       )
        


#def combined_salt(user_salt):
#    """Combine the master salt with the user salt...we use two seperate salts so that if the database is compromised, the
#    salts aren't immediately known"""
#    secret_salt = app.confing['SECRET_SALT']
#    assert len(user_salt) == 32
#    assert len(secret_salt) == 32
#    combined = ""
#    for x, y in user_salt, secret_salt:
#        combined = combined + x + y
#    return combined
    


class GroupsManager(object):
    def __init__(self, kw):
        self.datasets = create_datasets_list()


class RolesManager(object):
    def __init__(self):
        self.roles = model.Role.query.all()
        print("Roles are:", self.roles)


#class Password(object):
#    """To generate a master password: dd if=/dev/urandom bs=32 count=1 > master_salt"""
#    
#    master_salt = 




