"""Entry point for flask app"""
# pylint: disable=C0413,E0611
import time
from typing import Tuple
from urllib.parse import urljoin, urlparse

import redis
import jinja2
import werkzeug
from flask_session import Session
from authlib.integrations.requests_client import OAuth2Session
from flask import g, Flask, flash, session, url_for, redirect, current_app

from base import webqtlConfig
from utility import formatting
from utility.hmac import data_hmac, url_for_hmac
from utility.configuration import tempdir, override_from_envvars

from gn3.authentication import DataRole, AdminRole

from wqflask.database import parse_db_url

from wqflask.group_manager import group_management
from wqflask.resource_manager import resource_management
from wqflask.metadata_edits import metadata_edit

from wqflask.top_level_routes import toplevel
from wqflask.api.markdown import glossary_blueprint
from wqflask.api.markdown import references_blueprint
from wqflask.api.markdown import links_blueprint
from wqflask.api.markdown import policies_blueprint
from wqflask.api.markdown import environments_blueprint
from wqflask.api.markdown import facilities_blueprint
from wqflask.api.markdown import blogs_blueprint
from wqflask.api.markdown import news_blueprint
from wqflask.api.jobs import jobs as jobs_bp
from wqflask.oauth2.routes import oauth2
from wqflask.oauth2.checks import user_logged_in
from wqflask.oauth2.collections import num_collections
from wqflask.oauth2.request_utils import user_details, authserver_authorise_uri

from wqflask.jupyter_notebooks import jupyter_notebooks

app = Flask(__name__)


# See http://flask.pocoo.org/docs/config/#configuring-from-files
# Note no longer use the badly named WQFLASK_OVERRIDES (nyi)
app.config.from_envvar('GN2_SETTINGS')

DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT = parse_db_url(app.config.get('SQL_URI'))
app.config["DB_HOST"] = DB_HOST
app.config["DB_USER"] = DB_USER
app.config["DB_PASS"] = DB_PASS
app.config["DB_NAME"] = DB_NAME
app.config["DB_PORT"] = DB_PORT

app.jinja_env.globals.update(
    undefined=jinja2.StrictUndefined,
    numify=formatting.numify,
    logged_in=user_logged_in,
    authserver_authorise_uri=authserver_authorise_uri,
    user_details=user_details,
    num_collections=num_collections,
    url_for_hmac=url_for_hmac,
    data_hmac=data_hmac)

app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])

# Override settings
app = override_from_envvars(app)
app.config["TEMPDIR"] = tempdir(app)
app = webqtlConfig.init_app(app)

# Registering blueprints
app.register_blueprint(toplevel)
app.register_blueprint(glossary_blueprint, url_prefix="/glossary")
app.register_blueprint(references_blueprint, url_prefix="/references")
app.register_blueprint(links_blueprint, url_prefix="/links")
app.register_blueprint(policies_blueprint, url_prefix="/policies")
app.register_blueprint(environments_blueprint, url_prefix="/environments")
app.register_blueprint(facilities_blueprint, url_prefix="/facilities")
app.register_blueprint(blogs_blueprint, url_prefix="/blogs")
app.register_blueprint(news_blueprint, url_prefix="/news")
app.register_blueprint(jupyter_notebooks, url_prefix="/jupyter_notebooks")

app.register_blueprint(resource_management, url_prefix="/resource-management")
app.register_blueprint(metadata_edit, url_prefix="/datasets/")
app.register_blueprint(group_management, url_prefix="/group-management")
app.register_blueprint(jobs_bp, url_prefix="/jobs")
app.register_blueprint(oauth2, url_prefix="/oauth2")

from wqflask.decorators import AuthorisationError
from wqflask.app_errors import (
    handle_generic_exceptions, handle_authorisation_error)
app.register_error_handler(Exception, handle_generic_exceptions)
app.register_error_handler(AuthorisationError, handle_authorisation_error)

server_session = Session(app)

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

    token = session.get("oauth2_token", False)
    if token and not bool(session.get("user_details", False)):
        config = current_app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            token=token)
        resp = client.get(
            urljoin(config["GN_SERVER_URL"], "oauth2/user"))
        user_details = resp.json()
        session["user_details"] = user_details

        if user_details.get("error") == "invalid_token":
            flash(user_details["error_description"], "alert-danger")
            flash("You are now logged out.", "alert-info")
            session.pop("user_details", None)
            session.pop("oauth2_token", None)

@app.context_processor
def include_admin_role_class():
    return {'AdminRole': AdminRole}


@app.context_processor
def include_data_role_class():
    return {'DataRole': DataRole}


from wqflask import group_manager
from wqflask import resource_manager
from wqflask import search_results
from wqflask import export_traits
from wqflask import gsearch
from wqflask import update_search_results
from wqflask import docs
from wqflask import db_info
from wqflask import user_login
from wqflask import user_session

import wqflask.views
import wqflask.partial_correlations_views
