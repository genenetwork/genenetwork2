import os
import hashlib
import datetime
import time
import logging
import uuid
import hmac
import base64
import requests

import simplejson as json

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash, abort)

from wqflask import app
from wqflask import pbkdf2
from wqflask.user_session import UserSession

from utility import hmac
from utility.redis_tools import is_redis_available, get_redis_conn, get_user_id, get_user_by_unique_column, set_user_attribute, save_user, save_verification_code, check_verification_code, get_user_collections, save_collections
Redis = get_redis_conn()

from utility.logger import getLogger
logger = getLogger(__name__)

from smtplib import SMTP
from utility.tools import SMTP_CONNECT, SMTP_USERNAME, SMTP_PASSWORD, LOG_SQL_ALCHEMY, GN2_BRANCH_URL

THREE_DAYS = 60 * 60 * 24 * 3

def timestamp():
    return datetime.datetime.utcnow().isoformat()

def basic_info():
    return dict(timestamp = timestamp(),
                ip_address = request.remote_addr,
                user_agent = request.headers.get('User-Agent'))


def encode_password(pass_gen_fields, unencrypted_password):
    if isinstance(pass_gen_fields['salt'], bytes):
        salt = pass_gen_fields['salt']
    else:
        salt = bytes(pass_gen_fields['salt'], "utf-8")
    encrypted_password = pbkdf2.pbkdf2_hex(str(unencrypted_password), 
                                           salt,
                                           pass_gen_fields['iterations'], 
                                           pass_gen_fields['keylength'], 
                                           pass_gen_fields['hashfunc'])

    pass_gen_fields.pop("unencrypted_password", None)
    pass_gen_fields["password"] = encrypted_password

    return pass_gen_fields

def set_password(password):
    pass_gen_fields = {
      "unencrypted_password": password,
      "algorithm": "pbkdf2",
      "hashfunc": "sha256",
      "salt": base64.b64encode(os.urandom(32)),
      "iterations": 100000,
      "keylength": 32,
      "created_timestamp": timestamp()
    }

    assert len(password) >= 6, "Password shouldn't be shorter than 6 characters"

    encoded_password = encode_password(pass_gen_fields, pass_gen_fields['unencrypted_password'])

    return encoded_password

def get_signed_session_id(user):
    session_id = str(uuid.uuid4())

    session_id_signature = hmac.hmac_creation(session_id)
    session_id_signed = session_id + ":" + session_id_signature

    #ZS: Need to check if this is ever actually used or exists
    if 'user_id' not in user:
        user['user_id'] = str(uuid.uuid4())
        save_user(user, user['user_id'])

    if 'github_id' in user:
        session = dict(login_time = time.time(),
                    user_type = "github",
                    user_id = user['user_id'],
                    github_id = user['github_id'],
                    user_name = user['name'],
                    user_url = user['user_url'])
    elif 'orcid' in user:
        session = dict(login_time = time.time(),
                    user_type = "orcid",
                    user_id = user['user_id'],
                    github_id = user['orcid'],
                    user_name = user['name'],
                    user_url = user['user_url'])
    else:
        session = dict(login_time = time.time(),
                       user_type = "gn2",
                       user_id = user['user_id'],
                       user_name = user['full_name'],
                       user_email_address = user['email_address'])

    key = UserSession.user_cookie_name + ":" + session_id
    Redis.hmset(key, session)
    Redis.expire(key, THREE_DAYS)
    
    return session_id_signed

def send_email(toaddr, msg, fromaddr="no-reply@genenetwork.org"):
    """Send an E-mail through SMTP_CONNECT host. If SMTP_USERNAME is not
    'UNKNOWN' TLS is used

    """
    if SMTP_USERNAME == 'UNKNOWN':
        server = SMTP(SMTP_CONNECT)
        server.sendmail(fromaddr, toaddr, msg)
    else:
        server = SMTP(SMTP_CONNECT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(fromaddr, toaddr, msg)
        server.quit()
    logger.info("Successfully sent email to "+toaddr)

def send_verification_email(user_details, template_name = "email/user_verification.txt", key_prefix = "verification_code", subject = "GeneNetwork e-mail verification"):
    verification_code = str(uuid.uuid4())
    key = key_prefix + ":" + verification_code

    data = json.dumps(dict(id=user_details['user_id'], timestamp = timestamp()))

    Redis.set(key, data)
    Redis.expire(key, THREE_DAYS)

    recipient = user_details['email_address']
    body = render_template(template_name, verification_code = verification_code)
    send_email(recipient, subject, body)
    return {"recipient": recipient, "subject": subject, "body": body}

def send_invitation_email(user_email, temp_password, template_name = "email/user_invitation.txt",  subject = "You've been added to a GeneNetwork user group"):
    recipient = user_email
    body = render_template(template_name, temp_password)
    send_email(recipient, subject, body)
    return {"recipient": recipient, "subject": subject, "body": body}

@app.route("/manage/verify_email")
def verify_email():
    if 'code' in request.args:
        user_details = check_verification_code(request.args['code'])
        if user_details:
            # As long as they have access to the email account
            # We might as well log them in
            session_id_signed = get_signed_session_id(user_details)
            flash("Thank you for logging in {}.".format(user_details['full_name']), "alert-success")
            response = make_response(redirect(url_for('index_page', import_collections = import_col, anon_id = anon_id)))
            response.set_cookie(UserSession.user_cookie_name, session_id_signed, max_age=None)
            return response
        else:
            flash("Invalid code: Password reset code does not exist or might have expired!", "error")

@app.route("/n/login", methods=('GET', 'POST'))
def login():
    params = request.form if request.form else request.args
    logger.debug("in login params are:", params)

    if not params: #ZS: If coming to page for first time
        from utility.tools import GITHUB_AUTH_URL, GITHUB_CLIENT_ID, ORCID_AUTH_URL, ORCID_CLIENT_ID
        external_login = {}
        if GITHUB_AUTH_URL and GITHUB_CLIENT_ID != 'UNKNOWN':
            external_login["github"] = GITHUB_AUTH_URL
        if ORCID_AUTH_URL and ORCID_CLIENT_ID != 'UNKNOWN':
            external_login["orcid"] = ORCID_AUTH_URL
        return render_template("new_security/login_user.html", external_login = external_login, redis_is_available=is_redis_available())
    else: #ZS: After clicking sign-in
        if 'type' in params and 'uid' in params:
            user_details = get_user_by_unique_column("user_id", params['uid'])
            if user_details:
                session_id_signed = get_signed_session_id(user_details)
                if 'name' in user_details and user_details['name'] != "None":
                    display_id = user_details['name']
                elif 'github_id' in user_details:
                    display_id = user_details['github_id']
                elif 'orcid' in user_details:
                    display_id = user_details['orcid']
                else:
                    display_id = ""
                flash("Thank you for logging in {}.".format(display_id), "alert-success")
                response = make_response(redirect(url_for('index_page')))
                response.set_cookie(UserSession.user_cookie_name, session_id_signed, max_age=None)
            else:
                flash("Something went unexpectedly wrong.", "alert-danger")
                response = make_response(redirect(url_for('index_page')))  
            return response
        else:
            user_details = get_user_by_unique_column("email_address", params['email_address'])
            password_match = False
            if user_details:
                submitted_password = params['password']
                pwfields = user_details['password']
                if isinstance(pwfields, str):
                    pwfields = json.loads(pwfields)
                encrypted_pass_fields = encode_password(pwfields, submitted_password)
                password_match = pbkdf2.safe_str_cmp(encrypted_pass_fields['password'], pwfields['password'])

            else: # Invalid e-mail
                flash("Invalid e-mail address. Please try again.", "alert-danger")
                response = make_response(redirect(url_for('login')))

                return response
            if password_match: # If password correct
                if user_details['confirmed']: # If account confirmed
                    import_col = "false"
                    anon_id = ""
                    if 'import_collections' in params:
                        import_col = "true"
                        anon_id = params['anon_id']

                    session_id_signed = get_signed_session_id(user_details)
                    flash("Thank you for logging in {}.".format(user_details['full_name']), "alert-success")
                    response = make_response(redirect(url_for('index_page', import_collections = import_col, anon_id = anon_id)))
                    response.set_cookie(UserSession.user_cookie_name, session_id_signed, max_age=None)
                    return response
                else:
                    email_ob = send_verification_email(user_details, template_name = "email/user_verification.txt")
                    return render_template("newsecurity/verification_still_needed.html", subject=email_ob['subject'])
            else: # Incorrect password
                #ZS: It previously seemed to store that there was an incorrect log-in attempt here, but it did so in the MySQL DB so this might need to be reproduced with Redis
                flash("Invalid password. Please try again.", "alert-danger")
                response = make_response(redirect(url_for('login')))

                return response

@app.route("/n/login/github_oauth2", methods=('GET', 'POST'))
def github_oauth2():
    from utility.tools import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_AUTH_URL
    code = request.args.get("code")
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code
    }

    result = requests.post("https://github.com/login/oauth/access_token", json=data)
    result_dict = {arr[0]:arr[1] for arr in [tok.split("=") for tok in result.text.split("&")]}

    github_user = get_github_user_details(result_dict["access_token"])

    user_details = get_user_by_unique_column("github_id", github_user["id"])
    if user_details == None:
        user_details = {
            "user_id": str(uuid.uuid4()), 
            "name": github_user["name"].encode("utf-8") if github_user["name"] else "None", 
            "github_id": github_user["id"],
            "user_url": github_user["html_url"].encode("utf-8"), 
            "login_type": "github", 
            "organization": "", 
            "active": 1, 
            "confirmed": 1
        }
        save_user(user_details, user_details["user_id"])

    url = "/n/login?type=github&uid="+user_details["user_id"]
    return redirect(url)

def get_github_user_details(access_token):
    from utility.tools import GITHUB_API_URL
    result = requests.get(GITHUB_API_URL, headers = {'Authorization':'token ' + access_token }).content

    return json.loads(result)

@app.route("/n/login/orcid_oauth2", methods=('GET', 'POST'))
def orcid_oauth2():
    from uuid import uuid4
    from utility.tools import ORCID_CLIENT_ID, ORCID_CLIENT_SECRET, ORCID_TOKEN_URL, ORCID_AUTH_URL
    code = request.args.get("code")
    error = request.args.get("error")
    url = "/n/login"
    if code:
        data = {
            "client_id": ORCID_CLIENT_ID, 
            "client_secret": ORCID_CLIENT_SECRET, 
            "grant_type": "authorization_code",
            "redirect_uri": GN2_BRANCH_URL + "n/login/orcid_oauth2",
            "code": code
        }

        result = requests.post(ORCID_TOKEN_URL, data=data)
        result_dict = json.loads(result.text.encode("utf-8"))

        user_details = get_user_by_unique_column("orcid", result_dict["orcid"])
        if user_details == None:
            user_details = {
                "user_id": str(uuid4()), 
                "name": result_dict["name"], 
                "orcid": result_dict["orcid"], 
                "user_url": "%s/%s" % ("/".join(ORCID_AUTH_URL.split("/")[:-2]), result_dict["orcid"]), 
                "login_type": "orcid", 
                "organization": "", 
                "active": 1, 
                "confirmed": 1
            }
            save_user(user_details, user_details["user_id"])

        url = "/n/login?type=orcid&uid="+user_details["user_id"]
    else:
        flash("There was an error getting code from ORCID")
    return redirect(url)

def get_github_user_details(access_token):
    from utility.tools import GITHUB_API_URL
    result = requests.get(GITHUB_API_URL, headers = {'Authorization':'token ' + access_token }).content

    return json.loads(result)


@app.route("/n/logout")
def logout():
    logger.debug("Logging out...")
    UserSession().delete_session()
    flash("You are now logged out. We hope you come back soon!")
    response = make_response(redirect(url_for('index_page')))
    # Delete the cookie
    response.set_cookie(UserSession.user_cookie_name, '', expires=0)
    return response

@app.route("/n/forgot_password", methods=['GET'])
def forgot_password():
    """Entry point for forgotten password"""
    print("ARGS: ", request.args)
    errors = {"no-email": request.args.get("no-email")}
    print("ERRORS: ", errors)
    return render_template("new_security/forgot_password.html", errors=errors)

def send_forgot_password_email(verification_email):
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText

    template_name  = "email/forgot_password.txt"
    key_prefix = "forgot_password_code"
    subject = "GeneNetwork password reset"
    fromaddr = "no-reply@genenetwork.org"
    
    verification_code = str(uuid.uuid4())
    key = key_prefix + ":" + verification_code

    data = {
        "verification_code": verification_code,
        "email_address": verification_email,
        "timestamp": timestamp()
    }

    save_verification_code(verification_email, verification_code)

    body = render_template(template_name, verification_code = verification_code)

    msg = MIMEMultipart()
    msg["To"] = verification_email
    msg["Subject"] = subject
    msg["From"] = fromaddr
    msg.attach(MIMEText(body, "plain"))

    send_email(verification_email, msg.as_string())

    return subject

@app.route("/n/forgot_password_submit", methods=('POST',))
def forgot_password_submit():
    """When a forgotten password form is submitted we get here"""
    params = request.form
    email_address = params['email_address']
    next_page = None
    if email_address != "":
        logger.debug("Wants to send password E-mail to ", email_address)
        user_details = get_user_by_unique_column("email_address", email_address)
        if user_details:
            email_subject = send_forgot_password_email(user_details["email_address"])
            return render_template("new_security/forgot_password_step2.html",
                                   subject=email_subject)
        else:
            flash("The e-mail entered is not associated with an account.", "alert-danger")
            return redirect(url_for("forgot_password"))

    else:
        flash("You MUST provide an email", "alert-danger")
        return redirect(url_for("forgot_password"))

@app.route("/n/password_reset", methods=['GET'])
def password_reset():
    """Entry point after user clicks link in E-mail"""
    logger.debug("in password_reset request.url is:", request.url)

    verification_code = request.args.get('code')
    hmac = request.args.get('hm')

    if verification_code:
        user_details = check_verification_code(verification_code)
        if user_details:
            return render_template(
                "new_security/password_reset.html", user_encode=user_details["email_address"])
        else:
            flash("Invalid code: Password reset code does not exist or might have expired!", "error")
            return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))

@app.route("/n/password_reset_step2", methods=('POST',))
def password_reset_step2():
    """Handle confirmation E-mail for password reset"""
    logger.debug("in password_reset request.url is:", request.url)

    errors = []
    user_email = request.form['user_encode']
    user_id = get_user_id("email_address", user_email)

    password = request.form['password']
    encoded_password = set_password(password)

    set_user_attribute(user_id, "password", encoded_password)

    flash("Password changed successfully. You can now sign in.", "alert-info")
    return redirect(url_for('login'))

def register_user(params):
        thank_you_mode = False
        errors = []
        user_details = {}

        user_details['email_address'] = params.get('email_address', '').encode("utf-8").strip()
        if not (5 <= len(user_details['email_address']) <= 50):
            errors.append('Email Address needs to be between 5 and 50 characters.')
        else:
            email_exists = get_user_by_unique_column("email_address", user_details['email_address'])
            if email_exists:
                errors.append('User already exists with that email')

        user_details['full_name'] = params.get('full_name', '').encode("utf-8").strip()
        if not (5 <= len(user_details['full_name']) <= 50):
            errors.append('Full Name needs to be between 5 and 50 characters.')

        user_details['organization'] = params.get('organization', '').encode("utf-8").strip()
        if user_details['organization'] and not (5 <= len(user_details['organization']) <= 50):
            errors.append('Organization needs to be empty or between 5 and 50 characters.')

        password = str(params.get('password', ''))
        if not (6 <= len(password)):
            errors.append('Password needs to be at least 6 characters.')

        if params.get('password_confirm') != password:
            errors.append("Passwords don't match.")

        user_details['password'] = set_password(password)
        user_details['user_id'] = str(uuid.uuid4())
        user_details['confirmed'] = 1

        user_details['registration_info'] = basic_info()

        if len(errors) == 0:
            save_user(user_details, user_details['user_id'])

        return errors

@app.route("/n/register", methods=('GET', 'POST'))
def register():
    errors = []

    params = request.form if request.form else request.args
    params = params.to_dict(flat=True)

    if params:
        logger.debug("Attempting to register the user...")
        errors = register_user(params)

        if len(errors) == 0:
            flash("Registration successful. You may login with your new account", "alert-info")
            return redirect(url_for("login"))

    return render_template("new_security/register_user.html", values=params, errors=errors)

@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))
