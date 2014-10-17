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



from base.data_set import create_datasets_list

THREE_DAYS = 60 * 60 * 24 * 3
#THREE_DAYS = 45

def timestamp():
    return datetime.datetime.utcnow().isoformat()


class AnonUser(object):
    cookie_name = 'anon_user_v1'
    
    def __init__(self):
        self.cookie = request.cookies.get(self.cookie_name)
        if self.cookie:
            print("already is cookie")
            self.anon_id = verify_cookie(self.cookie)
        else:
            print("creating new cookie")
            self.anon_id, self.cookie = create_signed_cookie()
            
        @after.after_this_request
        def set_cookie(response):
            response.set_cookie(self.cookie_name, self.cookie)


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
    print("uuid_signed:", uuid_signed)
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
            print("self.redis_key is:", self.redis_key)
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
                print("Extending ttl...")
                Redis.expire(self.redis_key, THREE_DAYS)
            
            print("record is:", self.record)
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
            # Already did this before
            return self.db_object
        except AttributeError:
            # Doesn't exist so we'll create it
            self.db_object = model.User.query.get(self.user_id)
            return self.db_object


    def delete_session(self):
        # And more importantly delete the redis record
        Redis.delete(self.cookie_name)
        print("At end of delete_session")

@app.before_request
def before_request():
    g.user_session = UserSession()

class UsersManager(object):
    def __init__(self):
        self.users = model.User.query.all()
        print("Users are:", self.users)


class UserManager(object):
    def __init__(self, kw):
        self.user_id = kw['user_id']
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

        print("No errors!")

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

        print("Adding verification email to queue")
        #self.send_email_verification()
        VerificationEmail(self.new_user)
        print("Added verification email to queue")

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

    print("pwfields:", vars(pwfields))
    print("locals:", locals())

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
        print("hashfunc is:", hashfunc)
        # On our computer it takes around 1.4 seconds in 2013
        start_time = time.time()
        salt = base64.b64decode(salt)
        self.password = pbkdf2.pbkdf2_hex(str(unencrypted_password),
                                          salt, iterations, keylength, hashfunc)
        self.encrypt_time = round(time.time() - start_time, 3)
        print("Creating password took:", self.encrypt_time)


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
    print("in password_reset request.url is:", request.url)

    # We do this mainly just to assert that it's in proper form for displaying next page
    # Really not necessary but doesn't hurt
    user_encode = DecodeUser(ForgotPasswordEmail.key_prefix).reencode_standalone()

    return render_template("new_security/password_reset.html", user_encode=user_encode)

@app.route("/n/password_reset_step2", methods=('POST',))
def password_reset_step2():
    print("in password_reset request.url is:", request.url)

    errors = []

    user_encode = request.form['user_encode']
    verification_code, separator, hmac = user_encode.partition(':')

    hmac_verified = actual_hmac_creation(verification_code)
    print("locals are:", locals())


    assert hmac == hmac_verified, "Someone has been naughty"

    user = DecodeUser.actual_get_user(ForgotPasswordEmail.key_prefix, verification_code)
    print("user is:", user)

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
        print("in get_coded_user, data is:", data)
        data = json.loads(data)
        print("data is:", data)
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
        print("in login params are:", params)
        if not params:
            return render_template("new_security/login_user.html")
        else:
            try:
                user = model.User.query.filter_by(email_address=params['email_address']).one()
            except sqlalchemy.orm.exc.NoResultFound:
                print("No account exists for that email address")
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
                print("\n\nComparing:\n{}\n{}\n".format(encrypted.password, pwfields.password))
                valid = pbkdf2.safe_str_cmp(encrypted.password, pwfields.password)
                print("valid is:", valid)

        if valid and not user.confirmed:
            VerificationEmail(user)
            return render_template("new_security/verification_still_needed.html",
                                   subject=VerificationEmail.subject)


        if valid:
            if params.get('remember'):
                print("I will remember you")
                self.remember_me = True

            return self.actual_login(user)

        else:
            if user:
                self.unsuccessful_login(user)
            flash("Invalid email-address or password. Please try again.", "alert-error")
            response = make_response(redirect(url_for('login')))

            return response

    def actual_login(self, user, assumed_by=None):
        """The meat of the logging in process"""
        session_id_signed = self.successful_login(user, assumed_by)
        flash("Thank you for logging in {}.".format(user.full_name), "alert-success")
        response = make_response(redirect(url_for('index_page')))
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
        print("session_id_signed:", session_id_signed)

        session = dict(login_time = time.time(),
                       user_id = user.id,
                       user_email_address = user.email_address)

        key = UserSession.cookie_name + ":" + login_rec.session_id
        print("Key when signing:", key)
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
    print("Logging out...")
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
        print("Attempting to register the user...")
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
    print("url passed in to verify is:", url)
    # Verify parts are correct at the end - we expect to see &hm= or ?hm= followed by an hmac
    assert url[-23:-20] == "hm=", "Unexpected url (stage 1)"
    assert url[-24] in ["?", "&"], "Unexpected url (stage 2)"
    hmac = url[-20:]
    url = url[:-24]  # Url without any of the hmac stuff

    #print("before urlsplit, url is:", url)
    #url = divide_up_url(url)[1]
    #print("after urlsplit, url is:", url)

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
        print("Roles are:", self.roles)
