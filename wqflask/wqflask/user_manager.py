from __future__ import print_function, division, absolute_import

"""Access things in template like this:

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

from sqlalchemy import orm

#from redis import StrictRedis
import redis
Redis = redis.StrictRedis()


from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash)

from wqflask import app


from pprint import pformat as pf

from wqflask import pbkdf2

from wqflask.database import db_session

from wqflask import model

from utility import Bunch, Struct



from base.data_set import create_datasets_list



def timestamp():
    return datetime.datetime.utcnow().isoformat()




class UserSession(object):
    cookie_name = 'session_id'

    def __init__(self):
        cookie = request.cookies.get(self.cookie_name)
        if not cookie:
            self.logged_in = False
            return
        else:
            session_id, separator, session_id_signature = cookie.partition(':')
            assert len(session_id) == 36, "Is session_id a uuid?"
            assert separator == ":", "Expected a : here"
            assert session_id_signature == actual_hmac_creation(session_id), "Uh-oh, someone tampering with the cookie?"
            self.redis_key = "session_id:" + session_id
            print("self.redis_key is:", self.redis_key)
            self.session_id = session_id
            self.record = Redis.hgetall(self.redis_key)
            print("record is:", self.record)
            self.logged_in = True


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

        set_password(password, user)

        self.user.registration_info = json.dumps(basic_info(), sort_keys=True)

        self.new_user = model.User(**self.user.__dict__)
        db_session.add(self.new_user)
        db_session.commit()

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
        two_days = 60 * 60 * 24 * 2
        Redis.expire(key, two_days)
        to = user.email_address
        subject = self.subject
        body = render_template(self.template_name,
                               verification_code = verification_code)
        send_email(to, subject, body)

class ForgotPasswordEmail(VerificationEmail):
    template_name = "email/forgot_password.txt"
    key_prefix = "forgot_password_code"
    subject = "GeneNetwork password reset"


class Password(object):
    def __init__(self, unencrypted_password, salt, iterations, keylength, hashfunc):
        hashfunc = getattr(hashlib, hashfunc)
        print("hashfunc is:", hashfunc)
        # On our computer it takes around 1.4 seconds in 2013
        start_time = time.time()
        salt = base64.b64decode(salt)
        print("now salt is:", salt)
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
    params = request.form if request.form else request.args
    print("in login params are:", params)
    if not params:
        return render_template("new_security/login_user.html")
    else:
        user = model.User.query.filter_by(email_address=params['email_address']).one()
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

        login_rec = model.Login(user)


        if valid:
            login_rec.successful = True
            login_rec.session_id = str(uuid.uuid4())
            #session_id = "session_id:{}".format(login_rec.session_id)
            session_id_signature = actual_hmac_creation(login_rec.session_id)
            session_id_signed = login_rec.session_id + ":" + session_id_signature
            print("session_id_signed:", session_id_signed)

            session = dict(login_time = time.time(),
                           user_id = user.id,
                           user_email_address = user.email_address)

            flash("Thank you for logging in {}.".format(user.full_name), "alert-success")

            key = "session_id:" + login_rec.session_id
            print("Key when signing:", key)
            Redis.hmset(key, session)

            response = make_response(redirect(url_for('index_page')))
            response.set_cookie(UserSession.cookie_name, session_id_signed)
        else:
            login_rec.successful = False
            flash("Invalid email-address or password. Please try again.", "alert-error")
            response = make_response(redirect(url_for('login')))
        db_session.add(login_rec)
        db_session.commit()
        return response

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



@app.route("/manage/users")
def manage_users():
    template_vars = UsersManager()
    return render_template("admin/user_manager.html", **template_vars.__dict__)

@app.route("/manage/user")
def manage_user():
    template_vars = UserManager(request.args)
    return render_template("admin/ind_user_manager.html", **template_vars.__dict__)

@app.route("/manage/groups")
def manage_groups():
    template_vars = GroupsManager(request.args)
    return render_template("admin/group_manager.html", **template_vars.__dict__)


@app.route("/n/register", methods=('GET', 'POST'))
def register():
    params = None
    errors = None

    #if request.form:
    #    params = request.form
    #else:
    #    params = request.args

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

app.jinja_env.globals.update(url_for_hmac=url_for_hmac)

#######################################################################################

def send_email(to, subject, body):
    msg = json.dumps(dict(From="no-reply@genenetwork.org",
                     To=to,
                     Subject=subject,
                     Body=body))
    Redis.rpush("mail_queue", msg)


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
