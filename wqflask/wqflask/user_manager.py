from __future__ import print_function, division, absolute_import

import os
import hashlib
import datetime
import time
import logging
import uuid
import hashlib
import hmac
import base64
import urlparse

import simplejson as json

#from redis import StrictRedis
import redis # used for collections
Redis = redis.StrictRedis()

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, abort)

from wqflask import app
from pprint import pformat as pf

from wqflask import pbkdf2 # password hashing
from wqflask.database import db_session
from wqflask import model

from utility import Bunch, Struct, after

import logging
from utility.logger import getLogger
logger = getLogger(__name__)

from base.data_set import create_datasets_list

import requests
from utility.elasticsearch_tools import get_elasticsearch_connection, get_user_by_unique_column, get_item_by_unique_column, save_user, es_save_data

from smtplib import SMTP
from utility.tools import SMTP_CONNECT, SMTP_USERNAME, SMTP_PASSWORD, LOG_SQL_ALCHEMY

THREE_DAYS = 60 * 60 * 24 * 3
#THREE_DAYS = 45

def timestamp():
    return datetime.datetime.utcnow().isoformat()

class AnonUser(object):
    """Anonymous user handling"""
    cookie_name = 'anon_user_v1'

    def __init__(self):
        self.cookie = request.cookies.get(self.cookie_name)
        if self.cookie:
            logger.debug("ANON COOKIE ALREADY EXISTS")
            self.anon_id = verify_cookie(self.cookie)
        else:
            logger.debug("CREATING NEW ANON COOKIE")
            self.anon_id, self.cookie = create_signed_cookie()

        self.key = "anon_collection:v1:{}".format(self.anon_id)

    def add_collection(self, new_collection):
        collection_dict = dict(name = new_collection.name,
                               created_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               changed_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               num_members = new_collection.num_members,
                               members = new_collection.get_members())

        Redis.set(self.key, json.dumps(collection_dict))
        Redis.expire(self.key, 60 * 60 * 24 * 30)

    def delete_collection(self, collection_name):
        existing_collections = self.get_collections()
        updated_collections = []
        for i, collection in enumerate(existing_collections):
            if collection['name'] == collection_name:
                continue
            else:
                this_collection = {}
                this_collection['id'] = collection['id']
                this_collection['name'] = collection['name']
                this_collection['created_timestamp'] = collection['created_timestamp'].strftime('%b %d %Y %I:%M%p')
                this_collection['changed_timestamp'] = collection['changed_timestamp'].strftime('%b %d %Y %I:%M%p')
                this_collection['num_members'] = collection['num_members']
                this_collection['members'] = collection['members']
                updated_collections.append(this_collection)

        Redis.set(self.key, json.dumps(updated_collections))

    def get_collections(self):
        json_collections = Redis.get(self.key)
        if json_collections == None or json_collections == "None":
            return []
        else:
            collections = json.loads(json_collections)
            for collection in collections:
                collection['created_timestamp'] = datetime.datetime.strptime(collection['created_timestamp'], '%b %d %Y %I:%M%p')
                collection['changed_timestamp'] = datetime.datetime.strptime(collection['changed_timestamp'], '%b %d %Y %I:%M%p')

            collections = sorted(collections, key = lambda i: i['changed_timestamp'], reverse = True)
            return collections

    def import_traits_to_user(self):
        result = Redis.get(self.key)
        collections_list = json.loads(result if result else "[]")
        for collection in collections_list:
            collection_exists = g.user_session.get_collection_by_name(collection['name'])
            if collection_exists:
                continue
            else:
                g.user_session.add_collection(collection['name'], collection['members'])

    def display_num_collections(self):
        """
        Returns the number of collections or a blank string if there are zero.

        Because this is so unimportant...we wrap the whole thing in a try/expect...last thing we
        want is a webpage not to be displayed because of an error here

        Importand TODO: use redis to cache this, don't want to be constantly computing it
        """
        try:
            num = len(self.get_collections())
            if num > 0:
                return num
            else:
                return ""
        except Exception as why:
            print("Couldn't display_num_collections:", why)
            return ""


def verify_cookie(cookie):
    the_uuid, separator, the_signature = cookie.partition(':')
    assert len(the_uuid) == 36, "Is session_id a uuid?"
    assert separator == ":", "Expected a : here"
    assert the_signature == actual_hmac_creation(the_uuid), "Uh-oh, someone tampering with the cookie?"
    return the_uuid

def create_signed_cookie():
    the_uuid = str(uuid.uuid4())
    signature = actual_hmac_creation(the_uuid)
    uuid_signed = the_uuid + ":" + signature
    logger.debug("uuid_signed:", uuid_signed)
    return the_uuid, uuid_signed

class UserSession(object):
    """Logged in user handling"""

    cookie_name = 'session_id_v1'

    def __init__(self):
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            logger.debug("NO USER COOKIE")
            self.logged_in = False
            return
        else:
            session_id = verify_cookie(cookie)

            self.redis_key = self.cookie_name + ":" + session_id
            logger.debug("self.redis_key is:", self.redis_key)
            self.session_id = session_id
            self.record = Redis.hgetall(self.redis_key)

            if not self.record:
                # This will occur, for example, when the browser has been left open over a long
                # weekend and the site hasn't been visited by the user
                self.logged_in = False

                ########### Grrr...this won't work because of the way flask handles cookies
                # Delete the cookie
                #response = make_response(redirect(url_for('login')))
                #response.set_cookie(self.cookie_name, '', expires=0)
                #flash(
                #   "Due to inactivity your session has expired. If you'd like please login again.")
                #return response
                return

            if Redis.ttl(self.redis_key) < THREE_DAYS:
                # (Almost) everytime the user does something we extend the session_id in Redis...
                logger.debug("Extending ttl...")
                Redis.expire(self.redis_key, THREE_DAYS)

            logger.debug("record is:", self.record)
            self.logged_in = True

    @property
    def user_id(self):
        """Shortcut to the user_id"""
        if 'user_id' in self.record:
            return self.record['user_id']
        else:
            return ''

    @property
    def es_user_id(self):
        """User id from ElasticSearch (need to check if this is the same as the id stored in self.records)"""

        es = get_elasticsearch_connection()
        user_email = self.record['user_email_address']

        #ZS: Get user's collections if they exist
        response = es.search(
                       index = "users", doc_type = "local", body = {
                       "query": { "match": { "email_address": user_email } }
                   })

        user_id = response['hits']['hits'][0]['_id']
        return user_id

    @property
    def user_name(self):
        """Shortcut to the user_name"""
        if 'user_name' in self.record:
            return self.record['user_name']
        else:
            return ''

    @property
    def user_collections(self):
        """List of user's collections"""

        es = get_elasticsearch_connection()

        user_email = self.record['user_email_address']

        #ZS: Get user's collections if they exist
        response = es.search(
                       index = "users", doc_type = "local", body = {
                       "query": { "match": { "email_address": user_email } }
                   })
        user_info = response['hits']['hits'][0]['_source']
        if 'collections' in user_info.keys():
            if len(user_info['collections']) > 0:
                collection_list = json.loads(user_info['collections'])
                return sorted(collection_list, key = lambda i: datetime.datetime.strptime(i['changed_timestamp'], '%b %d %Y %I:%M%p'), reverse=True)
            else:
                return []
        else:
            return []

    @property
    def num_collections(self):
        """Number of user's collections"""

        es = get_elasticsearch_connection()

        user_email = self.record['user_email_address']

        #ZS: Get user's collections if they exist
        response = es.search(
                       index = "users", doc_type = "local", body = {
                       "query": { "match": { "email_address": user_email } }
                   })

        user_info = response['hits']['hits'][0]['_source']
        logger.debug("USER NUM COLL:", user_info)
        if 'collections' in user_info.keys():
            if user_info['collections'] != "[]" and len(user_info['collections']) > 0:
                collections_json = json.loads(user_info['collections'])
                return len(collections_json)
            else:
                return 0
        else:
            return 0

###
# ZS: This is currently not used, but I'm leaving it here commented out because the old "set superuser" code (at the bottom of this file) used it
###
#    @property
#    def user_ob(self):
#        """Actual sqlalchemy record"""
#        # Only look it up once if needed, then store it
#        # raise "OBSOLETE: use ElasticSearch instead"
#        try:
#            if LOG_SQL_ALCHEMY:
#                logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
#
#            # Already did this before
#            return self.db_object
#        except AttributeError:
#            # Doesn't exist so we'll create it
#            self.db_object = model.User.query.get(self.user_id)
#            return self.db_object

    def add_collection(self, collection_name, traits):
        """Add collection into ElasticSearch"""

        collection_dict = {'id': unicode(uuid.uuid4()),
                           'name': collection_name,
                           'created_timestamp': datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                           'changed_timestamp': datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                           'num_members': len(traits),
                           'members': list(traits) }

        es = get_elasticsearch_connection()

        user_email = self.record['user_email_address']
        response = es.search(
                       index = "users", doc_type = "local", body = {
                       "query": { "match": { "email_address": user_email } }
                   })

        user_id = response['hits']['hits'][0]['_id']
        user_info = response['hits']['hits'][0]['_source']

        if 'collections' in user_info.keys():
            if user_info['collections'] != [] and user_info['collections'] != "[]":
                current_collections = json.loads(user_info['collections'])
                current_collections.append(collection_dict)
                self.update_collections(current_collections)
                #collections_json = json.dumps(current_collections)
            else:
                self.update_collections([collection_dict])
                #collections_json = json.dumps([collection_dict])
        else:
            self.update_collections([collection_dict])
            #collections_json = json.dumps([collection_dict])

        return collection_dict['id']

    def delete_collection(self, collection_id):
        """Remove collection with given ID"""

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                continue
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

        return collection['name']

    def add_traits_to_collection(self, collection_id, traits_to_add):
        """Add specified traits to a collection"""

        this_collection = self.get_collection_by_id(collection_id)

        updated_collection = this_collection
        updated_traits = this_collection['members'] + traits_to_add

        updated_collection['members'] = updated_traits
        updated_collection['num_members'] = len(updated_traits)
        updated_collection['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                updated_collections.append(updated_collection)
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

    def remove_traits_from_collection(self, collection_id, traits_to_remove):
        """Remove specified traits from a collection"""

        this_collection = self.get_collection_by_id(collection_id)

        updated_collection = this_collection
        updated_traits = []
        for trait in this_collection['members']:
            if trait in traits_to_remove:
                continue
            else:
                updated_traits.append(trait)

        updated_collection['members'] = updated_traits
        updated_collection['num_members'] = len(updated_traits)
        updated_collection['changed_timestamp'] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')

        updated_collections = []
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                updated_collections.append(updated_collection)
            else:
                updated_collections.append(collection)

        self.update_collections(updated_collections)

        return updated_traits

    def get_collection_by_id(self, collection_id):
        for collection in self.user_collections:
            if collection['id'] == collection_id:
                return collection

    def get_collection_by_name(self, collection_name):
        for collection in self.user_collections:
            if collection['name'] == collection_name:
                return collection

        return None

    def update_collections(self, updated_collections):
        es = get_elasticsearch_connection()

        collection_body = {'doc': {'collections': json.dumps(updated_collections)}}
        es.update(index='users', doc_type='local', id=self.es_user_id, refresh='wait_for', body=collection_body)

    def delete_session(self):
        # And more importantly delete the redis record
        Redis.delete(self.cookie_name)
        logger.debug("At end of delete_session")

@app.before_request
def before_request():
    g.user_session = UserSession()
    g.cookie_session = AnonUser()

@app.after_request
def set_cookie(response):
    if not request.cookies.get(g.cookie_session.cookie_name):
        response.set_cookie(g.cookie_session.cookie_name, g.cookie_session.cookie)
    return response

class UsersManager(object):
    def __init__(self):
        self.users = model.User.query.all()
        logger.debug("Users are:", self.users)

class UserManager(object):
    def __init__(self, kw):
        self.user_id = kw['user_id']
        logger.debug("In UserManager locals are:", pf(locals()))
        #self.user = model.User.get(user_id)
        #logger.debug("user is:", user)
        self.user = model.User.query.get(self.user_id)
        logger.debug("user is:", self.user)
        datasets = create_datasets_list()
        for dataset in datasets:
            if not dataset.check_confidentiality():
                continue
            logger.debug("\n  Name:", dataset.name)
            logger.debug("  Type:", dataset.type)
            logger.debug("  ID:", dataset.id)
            logger.debug("  Confidential:", dataset.check_confidentiality())
        #logger.debug("   ---> self.datasets:", self.datasets)


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

        self.user.registration_info = json.dumps(basic_info(), sort_keys=True)
        save_user(es, self.user.__dict__, self.user.user_id)

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


class VerificationEmail(object):
    template_name =  "email/verification.txt"
    key_prefix = "verification_code"
    subject = "GeneNetwork email verification"

    def __init__(self, user):
        verification_code = str(uuid.uuid4())
        key = self.key_prefix + ":" + verification_code

        data = json.dumps(dict(id=user.user_id,
                               timestamp=timestamp())
                          )

        Redis.set(key, data)
        #two_days = 60 * 60 * 24 * 2
        Redis.expire(key, THREE_DAYS)
        to = user.email_address
        subject = self.subject
        body = render_template(self.template_name,
                               verification_code = verification_code)
        send_email(to, subject, body)

class ForgotPasswordEmail(VerificationEmail):
    template_name = "email/forgot_password.txt"
    key_prefix = "forgot_password_code"
    subject = "GeneNetwork password reset"
    fromaddr = "no-reply@genenetwork.org"

    def __init__(self, toaddr):
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEText import MIMEText
        verification_code = str(uuid.uuid4())
        key = self.key_prefix + ":" + verification_code

        data = {
            "verification_code": verification_code,
            "email_address": toaddr,
            "timestamp": timestamp()
        }
        es = get_elasticsearch_connection()
        es_save_data(es, self.key_prefix, "local", data, verification_code)

        subject = self.subject
        body = render_template(
            self.template_name,
            verification_code = verification_code)

        msg = MIMEMultipart()
        msg["To"] = toaddr
        msg["Subject"] = self.subject
        msg["From"] = self.fromaddr
        msg.attach(MIMEText(body, "plain"))

        send_email(toaddr, msg.as_string())


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


def basic_info():
    return dict(timestamp = timestamp(),
                ip_address = request.remote_addr,
                user_agent = request.headers.get('User-Agent'))

@app.route("/manage/verify_email")
def verify_email():
    user = DecodeUser(VerificationEmail.key_prefix).user
    user.confirmed = json.dumps(basic_info(), sort_keys=True)
    db_session.commit()

    # As long as they have access to the email account
    # We might as well log them in

    session_id_signed = LoginUser().successful_login(user)
    response = make_response(render_template("new_security/thank_you.html"))
    response.set_cookie(UserSession.cookie_name, session_id_signed)
    return response

@app.route("/n/password_reset", methods=['GET'])
def password_reset():
    """Entry point after user clicks link in E-mail"""
    logger.debug("in password_reset request.url is:", request.url)
    # We do this mainly just to assert that it's in proper form for displaying next page
    # Really not necessary but doesn't hurt
    # user_encode = DecodeUser(ForgotPasswordEmail.key_prefix).reencode_standalone()
    verification_code = request.args.get('code')
    hmac = request.args.get('hm')
    es = get_elasticsearch_connection()
    if verification_code:
        code_details = get_item_by_unique_column(
            es
            , "verification_code"
            , verification_code
            , ForgotPasswordEmail.key_prefix
            , "local")
        if code_details:
            user_details = get_user_by_unique_column(
                es
                , "email_address"
                , code_details["email_address"])
            if user_details:
                return render_template(
                    "new_security/password_reset.html", user_encode=user_details["user_id"])
            else:
                flash("Invalid code: User no longer exists!", "error")
        else:
            flash("Invalid code: Password reset code does not exist or might have expired!", "error")
        return redirect(url_for("login"))#render_template("new_security/login_user.html", error=error)

@app.route("/n/password_reset_step2", methods=('POST',))
def password_reset_step2():
    """Handle confirmation E-mail for password reset"""
    logger.debug("in password_reset request.url is:", request.url)

    errors = []
    user_id = request.form['user_encode']

    logger.debug("locals are:", locals())


    user = Bunch()
    password = request.form['password']
    set_password(password, user)

    es = get_elasticsearch_connection()
    es.update(
        index = "users"
        , doc_type = "local"
        , id = user_id
        , body = {
            "doc": {
                "password": user.__dict__.get("password")
            }
        })

    flash("Password changed successfully. You can now sign in.", "alert-info")
    response = make_response(redirect(url_for('login')))

    return response

class DecodeUser(object):

    def __init__(self, code_prefix):
        verify_url_hmac(request.url)

        #params = urlparse.parse_qs(url)

        self.verification_code = request.args['code']
        self.user = self.actual_get_user(code_prefix, self.verification_code)

    def reencode_standalone(self):
        hmac = actual_hmac_creation(self.verification_code)
        return self.verification_code + ":" + hmac

    @staticmethod
    def actual_get_user(code_prefix, verification_code):
        data = Redis.get(code_prefix + ":" + verification_code)
        logger.debug("in get_coded_user, data is:", data)
        data = json.loads(data)
        logger.debug("data is:", data)
        return model.User.query.get(data['id'])

@app.route("/n/login", methods=('GET', 'POST'))
def login():
    lu = LoginUser()
    login_type = request.args.get("type")
    if login_type:
        uid = request.args.get("uid")
        return lu.oauth2_login(login_type, uid)
    else:
        return lu.standard_login()

@app.route("/n/login/github_oauth2", methods=('GET', 'POST'))
def github_oauth2():
    from utility.tools import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
    code = request.args.get("code")
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code
    }
    result = requests.post("https://github.com/login/oauth/access_token", json=data)
    result_dict = {arr[0]:arr[1] for arr in [tok.split("=") for tok in [token.encode("utf-8") for token in result.text.split("&")]]}

    github_user = get_github_user_details(result_dict["access_token"])
    es = get_elasticsearch_connection()
    user_details = get_user_by_unique_column(es, "github_id", github_user["id"])
    if user_details == None:
        user_details = {
            "user_id": str(uuid.uuid4())
            , "name": github_user["name"].encode("utf-8")
            , "github_id": github_user["id"]
            , "user_url": github_user["html_url"].encode("utf-8")
            , "login_type": "github"
            , "organization": ""
            , "active": 1
            , "confirmed": 1
        }
        save_user(es, user_details, user_details["user_id"])
    url = "/n/login?type=github&uid="+user_details["user_id"]
    return redirect(url)

@app.route("/n/login/orcid_oauth2", methods=('GET', 'POST'))
def orcid_oauth2():
    from uuid import uuid4
    from utility.tools import ORCID_CLIENT_ID, ORCID_CLIENT_SECRET, ORCID_TOKEN_URL, ORCID_AUTH_URL
    code = request.args.get("code")
    error = request.args.get("error")
    url = "/n/login"
    if code:
        data = {
            "client_id": ORCID_CLIENT_ID
            , "client_secret": ORCID_CLIENT_SECRET
            , "grant_type": "authorization_code"
            , "code": code
        }
        result = requests.post(ORCID_TOKEN_URL, data=data)
        result_dict = json.loads(result.text.encode("utf-8"))

        es = get_elasticsearch_connection()
        user_details = get_user_by_unique_column(es, "orcid", result_dict["orcid"])
        if user_details == None:
            user_details = {
                "user_id": str(uuid4())
                , "name": result_dict["name"]
                , "orcid": result_dict["orcid"]
                , "user_url": "%s/%s" % (
                    "/".join(ORCID_AUTH_URL.split("/")[:-2]),
                    result_dict["orcid"])
                , "login_type": "orcid"
                , "organization": ""
                , "active": 1
                , "confirmed": 1
            }
            save_user(es, user_details, user_details["user_id"])
        url = "/n/login?type=orcid&uid="+user_details["user_id"]
    else:
        flash("There was an error getting code from ORCID")
    return redirect(url)

def get_github_user_details(access_token):
    from utility.tools import GITHUB_API_URL
    result = requests.get(GITHUB_API_URL, params={"access_token":access_token})
    return result.json()

class LoginUser(object):
    remember_time = 60 * 60 * 24 * 30 # One month in seconds

    def __init__(self):
        self.remember_me = False
        self.logged_in = False

    def oauth2_login(self, login_type, user_id):
        """Login via an OAuth2 provider"""
        es = get_elasticsearch_connection()
        user_details = get_user_by_unique_column(es, "user_id", user_id)
        if user_details:
            user = model.User()
            user.id = user_details["user_id"] if user_details["user_id"] == None else "N/A"
            user.full_name = user_details["name"]
            user.login_type = user_details["login_type"]
            return self.actual_login(user)
        else:
            flash("Error logging in via OAuth2")
            return make_response(redirect(url_for('login')))

    def standard_login(self):
        """Login through the normal form"""
        params = request.form if request.form else request.args
        logger.debug("in login params are:", params)
        es = get_elasticsearch_connection()
        if not params:
            from utility.tools import GITHUB_AUTH_URL, GITHUB_CLIENT_ID, ORCID_AUTH_URL, ORCID_CLIENT_ID
            external_login = {}
            if GITHUB_AUTH_URL and GITHUB_CLIENT_ID != 'UNKNOWN':
                external_login["github"] = GITHUB_AUTH_URL
            if ORCID_AUTH_URL and ORCID_CLIENT_ID != 'UNKNOWN':
                external_login["orcid"] = ORCID_AUTH_URL
            assert(es is not None)
            return render_template(
                "new_security/login_user.html"
                , external_login=external_login
                , es_server=es.ping())
        else:
            user_details = get_user_by_unique_column(es, "email_address", params["email_address"])
            user = None
            valid = None
            if user_details:
                user = model.User();
                for key in user_details:
                    user.__dict__[key] = user_details[key]
                valid = False;

                submitted_password = params['password']
                pwfields = Struct(json.loads(user.password))
                encrypted = Password(
                    submitted_password,
                    pwfields.salt,
                    pwfields.iterations,
                    pwfields.keylength,
                    pwfields.hashfunc)
                logger.debug("\n\nComparing:\n{}\n{}\n".format(encrypted.password, pwfields.password))
                valid = pbkdf2.safe_str_cmp(encrypted.password, pwfields.password)
                logger.debug("valid is:", valid)

        if valid and not user.confirmed:
            VerificationEmail(user)
            return render_template("new_security/verification_still_needed.html",
                                   subject=VerificationEmail.subject)
        if valid:
            if params.get('remember'):
                logger.debug("I will remember you")
                self.remember_me = True

            if 'import_collections' in params:
                import_col = "true"
            else:
                import_col = "false"

            #g.cookie_session.import_traits_to_user()

            self.logged_in = True

            return self.actual_login(user, import_collections=import_col)

        else:
            if user:
                self.unsuccessful_login(user)
            flash("Invalid email-address or password. Please try again.", "alert-danger")
            response = make_response(redirect(url_for('login')))

            return response

    def actual_login(self, user, assumed_by=None, import_collections=None):
        """The meat of the logging in process"""
        session_id_signed = self.successful_login(user, assumed_by)
        flash("Thank you for logging in {}.".format(user.full_name), "alert-success")
        response = make_response(redirect(url_for('index_page', import_collections=import_collections)))
        if self.remember_me:
            max_age = self.remember_time
        else:
            max_age = None

        response.set_cookie(UserSession.cookie_name, session_id_signed, max_age=max_age)
        return response

    def successful_login(self, user, assumed_by=None):
        login_rec = model.Login(user)
        login_rec.successful = True
        login_rec.session_id = str(uuid.uuid4())
        login_rec.assumed_by = assumed_by
        #session_id = "session_id:{}".format(login_rec.session_id)
        session_id_signature = actual_hmac_creation(login_rec.session_id)
        session_id_signed = login_rec.session_id + ":" + session_id_signature
        logger.debug("session_id_signed:", session_id_signed)

        if not user.id:
            user.id = ''

        session = dict(login_time = time.time(),
                       user_id = user.id,
                       user_name = user.full_name,
                       user_email_address = user.email_address)

        key = UserSession.cookie_name + ":" + login_rec.session_id
        logger.debug("Key when signing:", key)
        Redis.hmset(key, session)
        if self.remember_me:
            expire_time = self.remember_time
        else:
            expire_time = THREE_DAYS
        Redis.expire(key, expire_time)

        return session_id_signed

    def unsuccessful_login(self, user):
        login_rec = model.Login(user)
        login_rec.successful = False
        db_session.add(login_rec)
        db_session.commit()

@app.route("/n/logout")
def logout():
    logger.debug("Logging out...")
    UserSession().delete_session()
    flash("You are now logged out. We hope you come back soon!")
    response = make_response(redirect(url_for('index_page')))
    # Delete the cookie
    response.set_cookie(UserSession.cookie_name, '', expires=0)
    return response


@app.route("/n/forgot_password", methods=['GET'])
def forgot_password():
    """Entry point for forgotten password"""
    print("ARGS: ", request.args)
    errors = {"no-email": request.args.get("no-email")}
    print("ERRORS: ", errors)
    return render_template("new_security/forgot_password.html", errors=errors)

@app.route("/n/forgot_password_submit", methods=('POST',))
def forgot_password_submit():
    """When a forgotten password form is submitted we get here"""
    params = request.form
    email_address = params['email_address']
    next_page = None
    if email_address != "":
        logger.debug("Wants to send password E-mail to ",email_address)
        es = get_elasticsearch_connection()
        user_details = get_user_by_unique_column(es, "email_address", email_address)
        if user_details:
            ForgotPasswordEmail(user_details["email_address"])
            return render_template("new_security/forgot_password_step2.html",
                                   subject=ForgotPasswordEmail.subject)
        else:
            flash("The e-mail entered is not associated with an account.", "alert-danger")
            return redirect(url_for("forgot_password"))

    else:
        flash("You MUST provide an email", "alert-danger")
        return redirect(url_for("forgot_password"))

@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))

###
# ZS: The following 6 functions require the old MySQL User accounts; I'm leaving them commented out just in case we decide to reimplement them using ElasticSearch
###
#def super_only():
#    try:
#        superuser = g.user_session.user_ob.superuser
#    except AttributeError:
#        superuser = False
#    if not superuser:
#        flash("You must be a superuser to access that page.", "alert-error")
#        abort(401)

#@app.route("/manage/users")
#def manage_users():
#    super_only()
#    template_vars = UsersManager()
#    return render_template("admin/user_manager.html", **template_vars.__dict__)

#@app.route("/manage/user")
#def manage_user():
#    super_only()
#    template_vars = UserManager(request.args)
#    return render_template("admin/ind_user_manager.html", **template_vars.__dict__)

#@app.route("/manage/groups")
#def manage_groups():
#    super_only()
#    template_vars = GroupsManager(request.args)
#    return render_template("admin/group_manager.html", **template_vars.__dict__)

#@app.route("/manage/make_superuser")
#def make_superuser():
#    super_only()
#    params = request.args
#    user_id = params['user_id']
#    user = model.User.query.get(user_id)
#    superuser_info = basic_info()
#    superuser_info['crowned_by'] = g.user_session.user_id
#    user.superuser = json.dumps(superuser_info, sort_keys=True)
#    db_session.commit()
#    flash("We've made {} a superuser!".format(user.name_and_org))
#    return redirect(url_for("manage_users"))

#@app.route("/manage/assume_identity")
#def assume_identity():
#    super_only()
#    params = request.args
#    user_id = params['user_id']
#    user = model.User.query.get(user_id)
#    assumed_by = g.user_session.user_id
#    return LoginUser().actual_login(user, assumed_by=assumed_by)


@app.route("/n/register", methods=('GET', 'POST'))
def register():
    params = None
    errors = None


    params = request.form if request.form else request.args
    params = params.to_dict(flat=True)
    es = get_elasticsearch_connection()
    params["es_connection"] = es

    if params:
        logger.debug("Attempting to register the user...")
        result = RegisterUser(params)
        errors = result.errors

        if len(errors) == 0:
            flash("Registration successful. You may login with your new account", "alert-info")
            return redirect(url_for("login"))

    return render_template("new_security/register_user.html", values=params, errors=errors)


################################# Sign and unsign #####################################

def url_for_hmac(endpoint, **values):
    """Like url_for but adds an hmac at the end to insure the url hasn't been tampered with"""

    url = url_for(endpoint, **values)

    hm = actual_hmac_creation(url)
    if '?' in url:
        combiner = "&"
    else:
        combiner = "?"
    return url + combiner + "hm=" + hm

def data_hmac(stringy):
    """Takes arbitray data string and appends :hmac so we know data hasn't been tampered with"""
    return stringy + ":" + actual_hmac_creation(stringy)


def verify_url_hmac(url):
    """Pass in a url that was created with url_hmac and this assures it hasn't been tampered with"""
    logger.debug("url passed in to verify is:", url)
    # Verify parts are correct at the end - we expect to see &hm= or ?hm= followed by an hmac
    assert url[-23:-20] == "hm=", "Unexpected url (stage 1)"
    assert url[-24] in ["?", "&"], "Unexpected url (stage 2)"
    hmac = url[-20:]
    url = url[:-24]  # Url without any of the hmac stuff

    #logger.debug("before urlsplit, url is:", url)
    #url = divide_up_url(url)[1]
    #logger.debug("after urlsplit, url is:", url)

    hm = actual_hmac_creation(url)

    assert hm == hmac, "Unexpected url (stage 3)"

def actual_hmac_creation(stringy):
    """Helper function to create the actual hmac"""

    secret = app.config['SECRET_HMAC_CODE']

    hmaced = hmac.new(secret, stringy, hashlib.sha1)
    hm = hmaced.hexdigest()
    # "Conventional wisdom is that you don't lose much in terms of security if you throw away up to half of the output."
    # http://www.w3.org/QA/2009/07/hmac_truncation_in_xml_signatu.html
    hm = hm[:20]
    return hm

app.jinja_env.globals.update(url_for_hmac=url_for_hmac,
                             data_hmac=data_hmac)

#######################################################################################

# def send_email(to, subject, body):
#     msg = json.dumps(dict(From="no-reply@genenetwork.org",
#                      To=to,
#                      Subject=subject,
#                      Body=body))
#     Redis.rpush("mail_queue", msg)

def send_email(toaddr, msg, fromaddr="no-reply@genenetwork.org"):
    """Send an E-mail through SMTP_CONNECT host. If SMTP_USERNAME is not
    'UNKNOWN' TLS is used

    """
    if SMTP_USERNAME == 'UNKNOWN':
        logger.debug("SMTP: connecting with host "+SMTP_CONNECT)
        server = SMTP(SMTP_CONNECT)
        server.sendmail(fromaddr, toaddr, msg)
    else:
        logger.debug("SMTP: connecting TLS with host "+SMTP_CONNECT)
        server = SMTP(SMTP_CONNECT)
        server.starttls()
        logger.debug("SMTP: login with user "+SMTP_USERNAME)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        logger.debug("SMTP: "+fromaddr)
        logger.debug("SMTP: "+toaddr)
        logger.debug("SMTP: "+msg)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
    logger.info("Successfully sent email to "+toaddr)

class GroupsManager(object):
    def __init__(self, kw):
        self.datasets = create_datasets_list()


class RolesManager(object):
    def __init__(self):
        self.roles = model.Role.query.all()
        logger.debug("Roles are:", self.roles)
