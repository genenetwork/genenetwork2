from __future__ import print_function, division, absolute_import

"""Used to Access things in template like this:
(BUT NOW OUT OF DATE)

    x: {{ g.identity.name }}
    security: {{ security.__dict__ }}

"""

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

import sqlalchemy
from sqlalchemy import orm

#from redis import StrictRedis
import redis
Redis = redis.StrictRedis()


from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, abort)

from wqflask import app


from pprint import pformat as pf

from wqflask import pbkdf2

from wqflask.database import db_session

from wqflask import model

from utility import Bunch, Struct, after
from utility.tools import LOG_SQL, LOG_SQLALCHEMY

import logging
from utility.logger import getLogger
logger = getLogger(__name__)

from base.data_set import create_datasets_list

THREE_DAYS = 60 * 60 * 24 * 3
#THREE_DAYS = 45

def timestamp():
    return datetime.datetime.utcnow().isoformat()


class AnonUser(object):
    cookie_name = 'anon_user_v8'

    def __init__(self):
        self.cookie = request.cookies.get(self.cookie_name)
        if self.cookie:
            logger.debug("already is cookie")
            self.anon_id = verify_cookie(self.cookie)
            
        else:
            logger.debug("creating new cookie")
            self.anon_id, self.cookie = create_signed_cookie()
        self.key = "anon_collection:v1:{}".format(self.anon_id)

        @after.after_this_request
        def set_cookie(response):
            response.set_cookie(self.cookie_name, self.cookie)
            
    def add_collection(self, new_collection):
        collection_dict = dict(name = new_collection.name,
                               created_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               changed_timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p'),
                               num_members = new_collection.num_members,
                               members = new_collection.get_members())
                               
        Redis.set(self.key, json.dumps(collection_dict))
        Redis.expire(self.key, 60 * 60 * 24 * 5)
            
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
            return collections
            
    def import_traits_to_user(self):
        collections_list = json.loads(Redis.get(self.key))
        for collection in collections_list:
            uc = model.UserCollection()
            uc.name = collection['name']
            collection_exists = g.user_session.user_ob.get_collection_by_name(uc.name)
            if collection_exists:
                continue
            else:
                uc.user = g.user_session.user_id
                uc.members = json.dumps(collection['members'])
                db_session.add(uc)
                db_session.commit()
            
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
    cookie_name = 'session_id_v2'

    def __init__(self):
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
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
    def user_ob(self):
        """Actual sqlalchemy record"""
        # Only look it up once if needed, then store it
        try:
            if LOG_SQLALCHEMY:
                logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

            # Already did this before
            return self.db_object
        except AttributeError:
            # Doesn't exist so we'll create it
            self.db_object = model.User.query.get(self.user_id)
            return self.db_object


    def delete_session(self):
        # And more importantly delete the redis record
        Redis.delete(self.cookie_name)
        logger.debug("At end of delete_session")

@app.before_request
def before_request():
    g.user_session = UserSession()
    g.cookie_session = AnonUser()
    
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

        logger.debug("No errors!")

        set_password(password, self.user)

        self.user.registration_info = json.dumps(basic_info(), sort_keys=True)

        self.new_user = model.User(**self.user.__dict__)
        db_session.add(self.new_user)

        try:
            db_session.commit()
        except sqlalchemy.exc.IntegrityError:
            # This exception is thrown if the email address is already in the database
            # To do: Perhaps put a link to sign in using an existing account here
            self.errors.append("An account with this email address already exists. "
                               "Click the button above to sign in using an existing account.")
            return

        logger.debug("Adding verification email to queue")
        #self.send_email_verification()
        VerificationEmail(self.new_user)
        logger.debug("Added verification email to queue")

        self.thank_you_mode = True


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

        data = json.dumps(dict(id=user.id,
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

    def __init__(self, user):
        verification_code = str(uuid.uuid4())
        key = self.key_prefix + ":" + verification_code

        data = json.dumps(dict(id=user.id,
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

@app.route("/n/password_reset")
def password_reset():
    logger.debug("in password_reset request.url is:", request.url)

    # We do this mainly just to assert that it's in proper form for displaying next page
    # Really not necessary but doesn't hurt
    user_encode = DecodeUser(ForgotPasswordEmail.key_prefix).reencode_standalone()

    return render_template("new_security/password_reset.html", user_encode=user_encode)

@app.route("/n/password_reset_step2", methods=('POST',))
def password_reset_step2():
    logger.debug("in password_reset request.url is:", request.url)

    errors = []

    user_encode = request.form['user_encode']
    verification_code, separator, hmac = user_encode.partition(':')

    hmac_verified = actual_hmac_creation(verification_code)
    logger.debug("locals are:", locals())


    assert hmac == hmac_verified, "Someone has been naughty"

    user = DecodeUser.actual_get_user(ForgotPasswordEmail.key_prefix, verification_code)
    logger.debug("user is:", user)

    password = request.form['password']

    set_password(password, user)
    db_session.commit()

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
    return lu.standard_login()


class LoginUser(object):
    remember_time = 60 * 60 * 24 * 30 # One month in seconds

    def __init__(self):
        self.remember_me = False

    def standard_login(self):
        """Login through the normal form"""
        params = request.form if request.form else request.args
        logger.debug("in login params are:", params)
        if not params:
            return render_template("new_security/login_user.html")
        else:
            try:
                user = model.User.query.filter_by(email_address=params['email_address']).one()
            except sqlalchemy.orm.exc.NoResultFound:
                logger.debug("No account exists for that email address")
                valid = False
                user = None
            else:
                submitted_password = params['password']
                pwfields = Struct(json.loads(user.password))
                encrypted = Password(submitted_password,
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
                
            return self.actual_login(user, import_collections=import_col)

        else:
            if user:
                self.unsuccessful_login(user)
            flash("Invalid email-address or password. Please try again.", "alert-error")
            response = make_response(redirect(url_for('login')))

            return response

    def actual_login(self, user, assumed_by=None, import_collections=None):
        """The meat of the logging in process"""
        session_id_signed = self.successful_login(user, assumed_by)
        flash("Thank you for logging in {}.".format(user.full_name), "alert-success")
        print("IMPORT1:", import_collections)
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

        session = dict(login_time = time.time(),
                       user_id = user.id,
                       user_email_address = user.email_address)

        key = UserSession.cookie_name + ":" + login_rec.session_id
        logger.debug("Key when signing:", key)
        Redis.hmset(key, session)
        if self.remember_me:
            expire_time = self.remember_time
        else:
            expire_time = THREE_DAYS
        Redis.expire(key, expire_time)
        db_session.add(login_rec)
        db_session.commit()
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


@app.route("/n/forgot_password")
def forgot_password():
    return render_template("new_security/forgot_password.html")

@app.route("/n/forgot_password_submit", methods=('POST',))
def forgot_password_submit():
    params = request.form
    email_address = params['email_address']
    try:
        user = model.User.query.filter_by(email_address=email_address).one()
    except orm.exc.NoResultFound:
        flash("Couldn't find a user associated with the email address {}. Sorry.".format(
            email_address))
        return redirect(url_for("login"))
    ForgotPasswordEmail(user)
    return render_template("new_security/forgot_password_step2.html",
                            subject=ForgotPasswordEmail.subject)

@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))

def super_only():
    try:
        superuser = g.user_session.user_ob.superuser
    except AttributeError:
        superuser = False
    if not superuser:
        flash("You must be a superuser to access that page.", "alert-error")
        abort(401)



@app.route("/manage/users")
def manage_users():
    super_only()
    template_vars = UsersManager()
    return render_template("admin/user_manager.html", **template_vars.__dict__)

@app.route("/manage/user")
def manage_user():
    super_only()
    template_vars = UserManager(request.args)
    return render_template("admin/ind_user_manager.html", **template_vars.__dict__)

@app.route("/manage/groups")
def manage_groups():
    super_only()
    template_vars = GroupsManager(request.args)
    return render_template("admin/group_manager.html", **template_vars.__dict__)

@app.route("/manage/make_superuser")
def make_superuser():
    super_only()
    params = request.args
    user_id = params['user_id']
    user = model.User.query.get(user_id)
    superuser_info = basic_info()
    superuser_info['crowned_by'] = g.user_session.user_id
    user.superuser = json.dumps(superuser_info, sort_keys=True)
    db_session.commit()
    flash("We've made {} a superuser!".format(user.name_and_org))
    return redirect(url_for("manage_users"))

@app.route("/manage/assume_identity")
def assume_identity():
    super_only()
    params = request.args
    user_id = params['user_id']
    user = model.User.query.get(user_id)
    assumed_by = g.user_session.user_id
    return LoginUser().actual_login(user, assumed_by=assumed_by)


@app.route("/n/register", methods=('GET', 'POST'))
def register():
    params = None
    errors = None


    params = request.form if request.form else request.args

    if params:
        logger.debug("Attempting to register the user...")
        result = RegisterUser(params)
        errors = result.errors

        if result.thank_you_mode:
            assert not errors, "Errors while in thank you mode? That seems wrong..."
            return render_template("new_security/registered.html",
                                   subject=VerificationEmail.subject)

    return render_template("new_security/register_user.html", values=params, errors=errors)




#@app.route("/n/login", methods=('GET', 'POST'))
#def login():
#    return user_manager.login()
#
#@app.route("/manage/verify")
#def verify():
#    user_manager.verify_email()
#    return render_template("new_security/verified.html")



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

def send_email(to, subject, body):
    msg = json.dumps(dict(From="no-reply@genenetwork.org",
                     To=to,
                     Subject=subject,
                     Body=body))
    Redis.rpush("mail_queue", msg)




class GroupsManager(object):
    def __init__(self, kw):
        self.datasets = create_datasets_list()


class RolesManager(object):
    def __init__(self):
        self.roles = model.Role.query.all()
        logger.debug("Roles are:", self.roles)
