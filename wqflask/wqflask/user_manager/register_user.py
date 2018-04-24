import os
import time
import uuid
import base64
import hashlib
import simplejson as json
from utility import Bunch
from flask import request
from wqflask import pbkdf2 # password hashing
from utility.elasticsearch_tools import get_user_by_unique_column, save_user
from utility.logger import getLogger

from .util_functions import timestamp

logger = getLogger(__name__)

class RegisterUser(object):
    def __init__(self, kw):
        self.thank_you_mode = False
        self.errors = []
        self.user = Bunch()
        es = kw.get('es_connection', None)

        if not es:
            self.errors.append("Missing connection object")

        self.user.email_address = kw.get('email_address', '').encode("utf-8").strip()
        if not (5 <= len(self.user.email_address) <= 50):
            self.errors.append('Email Address needs to be between 5 and 50 characters.')
        else:
            email_exists = get_user_by_unique_column(es, "email_address", self.user.email_address)
            if email_exists:
                self.errors.append('User already exists with that email')

        self.user.full_name = kw.get('full_name', '').encode("utf-8").strip()
        if not (5 <= len(self.user.full_name) <= 50):
            self.errors.append('Full Name needs to be between 5 and 50 characters.')

        self.user.organization = kw.get('organization', '').encode("utf-8").strip()
        if self.user.organization and not (5 <= len(self.user.organization) <= 50):
            self.errors.append('Organization needs to be empty or between 5 and 50 characters.')

        password = str(kw.get('password', ''))
        if not (6 <= len(password)):
            self.errors.append('Password needs to be at least 6 characters.')

        if kw.get('password_confirm') != password:
            self.errors.append("Passwords don't match.")

        if self.errors:
            return

        logger.debug("No errors!")

        set_password(password, self.user)
        self.user.user_id = str(uuid.uuid4())
        self.user.confirmed = 1
        save_user(es, self.user.__dict__, self.user.user_id)

class Password(object):
    def __init__(self, unencrypted_password, salt, iterations, keylength, hashfunc):
        hashfunc = getattr(hashlib, hashfunc)
        logger.debug("hashfunc is:", hashfunc)
        # On our computer it takes around 1.4 seconds in 2013
        start_time = time.time()
        salt = base64.b64decode(salt)
        self.password = pbkdf2.pbkdf2_hex(str(unencrypted_password),
                                          salt, iterations, keylength, hashfunc)
        self.encrypt_time = round(time.time() - start_time, 3)
        logger.debug("Creating password took:", self.encrypt_time)

def set_password(password, user):
    pwfields = Bunch()

    pwfields.algorithm = "pbkdf2"
    pwfields.hashfunc = "sha256"
    #hashfunc = getattr(hashlib, pwfields.hashfunc)

    # Encoding it to base64 makes storing it in json much easier
    pwfields.salt = base64.b64encode(os.urandom(32))

    # https://forums.lastpass.com/viewtopic.php?t=84104
    pwfields.iterations = 100000
    pwfields.keylength = 32

    pwfields.created_ts = timestamp()
    # One more check on password length
    assert len(password) >= 6, "Password shouldn't be so short here"

    logger.debug("pwfields:", vars(pwfields))
    logger.debug("locals:", locals())

    enc_password = Password(password,
                            pwfields.salt,
                            pwfields.iterations,
                            pwfields.keylength,
                            pwfields.hashfunc)

    pwfields.password = enc_password.password
    pwfields.encrypt_time = enc_password.encrypt_time

    user.password = json.dumps(pwfields.__dict__,
                                    sort_keys=True,
                                   )
