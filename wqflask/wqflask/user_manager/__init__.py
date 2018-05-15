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
                   redirect, flash, abort, session)

from wqflask import app
from pprint import pformat as pf

from wqflask import pbkdf2 # password hashing
from wqflask.database import db_session

from utility import Bunch, Struct

import logging
from utility.logger import getLogger
logger = getLogger(__name__)

from base.data_set import create_datasets_list

import requests
from utility.elasticsearch_tools import get_elasticsearch_connection, get_user_by_unique_column, get_item_by_unique_column, save_user, es_save_data

from smtplib import SMTP
from utility.tools import SMTP_CONNECT, SMTP_USERNAME, SMTP_PASSWORD

# local package imports
from .util_functions import actual_hmac_creation
from .anon_user import AnonUser
from .user_session import UserSession
from .register_user import RegisterUser, Password, set_password
from .util_functions import (timestamp, save_cookie_details, get_cookie_details,
                             delete_cookie_details, cookie_name, get_all_users)

THREE_DAYS = 60 * 60 * 24 * 3

@app.before_request
def before_request():
    from wqflask.collect import get_collections_by_user_key
    cookie_id = request.cookies.get(cookie_name)
    cookie = get_cookie_details(cookie_id)
    if cookie:
        session["user"] = cookie["user"]
        g.num_collections = len(
            get_collections_by_user_key(session["user"]["user_id"]))

    g.user_session = UserSession()
    g.cookie_session = AnonUser()

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

def basic_info():
    return dict(timestamp = timestamp(),
                ip_address = request.remote_addr,
                user_agent = request.headers.get('User-Agent'))

@app.route("/n/password_reset", methods=['GET'])
def password_reset():
    """Entry point after user clicks link in E-mail"""
    logger.debug("in password_reset request.url is:", request.url)
    # We do this mainly just to assert that it's in proper form for displaying next page
    # Really not necessary but doesn't hurt
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

@app.route("/n/login", methods=('GET', 'POST'))
def login():
    lu = LoginUser()
    return lu.standard_login()

@app.route("/n/login/github_oauth2/<import_collections>/<remember>", methods=('GET', 'POST'))
def github_oauth2(import_collections, remember):
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
            , "full_name": github_user["name"].encode("utf-8")
            , "github_id": github_user["id"]
            , "user_url": github_user["html_url"].encode("utf-8")
            , "login_type": "github"
            , "organization": ""
            , "active": 1
            , "confirmed": 1
        }
        save_user(es, user_details, user_details["user_id"])

    lu = LoginUser()
    lu.remember_me = (True if remember == "y" else False)
    return lu.oauth2_login(
        user_details["user_id"], import_collections=(
            import_collections if import_collections == "y" else None))

@app.route("/n/login/orcid_oauth2/<import_collections>/<remember>", methods=('GET', 'POST'))
def orcid_oauth2(import_collections, remember):
    from uuid import uuid4
    from utility.tools import ORCID_CLIENT_ID, ORCID_CLIENT_SECRET, ORCID_TOKEN_URL, ORCID_AUTH_URL
    code = request.args.get("code")
    error = request.args.get("error")
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
                , "full_name": result_dict["name"]
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
        lu = LoginUser()
        lu.remember_me = (True if remember == "y" else False)
        return lu.oauth2_login(
            user_details["user_id"], import_collections=(
                import_collections if import_collections == "y" else None))
    else:
        flash("There was an error getting code from ORCID")
        return redirect("/n/login")

def get_github_user_details(access_token):
    from utility.tools import GITHUB_API_URL
    result = requests.get(GITHUB_API_URL, params={"access_token":access_token})
    return result.json()

class LoginUser(object):
    remember_time = 60 * 60 * 24 * 30 # One month in seconds

    def __init__(self):
        self.remember_me = False

    def oauth2_login(self, user_id, import_collections):
        """Login via an OAuth2 provider"""
        es = get_elasticsearch_connection()
        user_details = get_user_by_unique_column(es, "user_id", user_id)
        if user_details:
            return self.actual_login(user=user_details, import_collections=(
                "true" if import_collections == "y" else "false"))
        else:
            flash("Error logging in via OAuth2")
            return make_response(redirect(url_for('login')))

    def local_sign_in(self, params):
        user_details = get_user_by_unique_column(
            es=get_elasticsearch_connection(), column_name="email_address",
            column_value=params["email_address"])
        user = None
        valid = None
        if user_details:
            user = Bunch()
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

            return self.actual_login(user_details, import_collections=import_col)
        else:
            flash("Invalid email-address or password. Please try again.", "alert-danger")
            response = make_response(redirect(url_for('login')))
            return response

    def github_sign_in(self, params):
        from utility.tools import GITHUB_AUTH_URL
        redirect_uri = url_for(
            "github_oauth2",
            import_collections=("y" if params.get("import_collections") else "n"),
            remember=("y" if params.get("remember") else "n"),
            _external=True)
        url = GITHUB_AUTH_URL + "&redirect_uri="+redirect_uri
        return redirect(url)

    def orcid_sign_in(self, params):
        from utility.tools import ORCID_AUTH_URL
        redirect_uri = url_for(
            "orcid_oauth2",
            import_collections=("y" if params.get("import_collections") else "n"),
            remember=("y" if params.get("remember") else "n"),
            _external=True)
        url = ORCID_AUTH_URL + "&redirect_uri="+redirect_uri
        return redirect(url)

    def standard_login(self):
        """Login through the normal form"""
        from utility.tools import GITHUB_AUTH_URL, GITHUB_CLIENT_ID, ORCID_AUTH_URL, ORCID_CLIENT_ID

        params = request.form if request.form else request.args
        logger.debug("in login params are:", params)
        es = get_elasticsearch_connection()
        if not params:
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
            login_type = params["submit"]
            login_types = {
                "Sign in": self.local_sign_in,
                "Sign in with GitHub": self.github_sign_in,
                "Sign in with ORCID": self.orcid_sign_in
            }
            return login_types[login_type](params)

    def actual_login(self, user, import_collections=None):
        """The meat of the logging in process"""
        session_id_signed = self.successful_login(user)
        flash("Thank you for logging in {}.".format(user["full_name"]), "alert-success")
        response = make_response(redirect(url_for('index_page', import_collections=import_collections)))
        if self.remember_me:
            max_age = self.remember_time
        else:
            max_age = None

        save_cookie_details(cookie_id=session_id_signed, user=user)
        response.set_cookie(UserSession.cookie_name, session_id_signed, max_age=max_age)
        return response

    def successful_login(self, user):
        session_id = str(uuid.uuid4())
        session_id_signature = actual_hmac_creation(session_id)
        session_id_signed = session_id + ":" + session_id_signature
        logger.debug("session_id_signed:", session_id_signed)
        session["user"] = user
        return session_id_signed

@app.route("/n/logout")
def logout():
    logger.debug("Logging out...")
    delete_cookie_details()
    session.pop("user")
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
        flash("You MUST provide an email", "alert-danger")
        return redirect(url_for("forgot_password"))

@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))

def super_only():
    try:
        superuser = session["user"].get("superuser", None)
    except AttributeError:
        superuser = False
    if not superuser:
        flash("You must be a superuser to access that page.", "alert-error")
        abort(401)



@app.route("/manage/users")
def manage_users():
    super_only()
    users = get_all_users()
    return render_template("admin/user_manager.html", users=users)

@app.route("/manage/user")
def manage_user():
    super_only()
    user = get_user_by_unique_column(
        es = get_elasticsearch_connection(), column_name="user_id",
        column_value=request.args["user_id"])
    crowner = None
    if user.get("superuser", None):
        crowner = get_user_by_unique_column(
            es = get_elasticsearch_connection(), column_name="user_id",
            column_value=user["superuser_info"]["crowned_by"])
    return render_template("admin/ind_user_manager.html", user=user,
                           crowner=crowner)

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
    user = get_user_by_unique_column(
        es = get_elasticsearch_connection(), column_name="user_id",
        column_value=user_id)
    user["superuser"] = True
    user["superuser_info"] = {
        "crowned_by": session["user"].get("user_id"),
        "timestamp": timestamp()
    }
    save_user(
        es = get_elasticsearch_connection(), user = user,
        user_id=user.get("user_id"))
    flash("We've made {} from {} a superuser!".format(
        user.get("full_name"),  user.get("organisation")))
    return redirect(url_for("manage_users"))

@app.route("/manage/assume_identity")
def assume_identity():
    super_only()
    params = request.args
    user_id = params['user_id']
    user = get_user_by_unique_column(
        es = get_elasticsearch_connection(), column_name="user_id",
        column_value=user_id)
    assumed_by = session["user"].get("user_id")
    return LoginUser().actual_login(user, assumed_by=assumed_by)


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
