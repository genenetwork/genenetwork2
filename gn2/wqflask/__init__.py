"""Entry point for flask app"""
# pylint: disable=C0413,E0611
import os
import sys
import time
import logging
import datetime
from typing import Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse

import redis
import jinja2
from flask_session import Session
from authlib.jose import JsonWebKey
from flask import g, Flask, flash, session, url_for, redirect, current_app


from gn2.utility import formatting

from gn3.authentication import DataRole, AdminRole

from gn2.wqflask.group_manager import group_management
from gn2.wqflask.resource_manager import resource_management
from gn2.wqflask.metadata_edits import metadata_edit
from gn2.wqflask.edit import metadata

from gn2.wqflask.api.markdown import glossary_blueprint
from gn2.wqflask.api.markdown import references_blueprint
from gn2.wqflask.api.markdown import links_blueprint
from gn2.wqflask.api.markdown import policies_blueprint
from gn2.wqflask.api.markdown import environments_blueprint
from gn2.wqflask.api.markdown import facilities_blueprint
from gn2.wqflask.api.markdown import blogs_blueprint
from gn2.wqflask.api.markdown import news_blueprint
from gn2.wqflask.api.markdown import xapian_syntax_blueprint
from gn2.wqflask.api.markdown import gn_docs_blueprint
from gn2.wqflask.api.jobs import jobs as jobs_bp
from gn2.wqflask.oauth2.routes import oauth2
from gn2.wqflask.oauth2.client import user_logged_in
from gn2.wqflask.oauth2.collections import num_collections
from gn2.wqflask.oauth2.request_utils import user_details, authserver_authorise_uri

from gn2.wqflask.jupyter_notebooks import jupyter_notebooks

from gn2.wqflask.startup import (
    StartupError,
    startup_errors,
    check_mandatory_configs)


def numcoll():
    """Handle possible errors."""
    try:
        return num_collections()
    except Exception as _exc:
        return "ERROR"


def dev_loggers(appl: Flask) -> None:
    """Default development logging."""
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s [%(thread)d -- %(threadName)s] in %(module)s: %(message)s")
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setFormatter(formatter)
    appl.logger.addHandler(stderr_handler)

    root_logger = logging.getLogger()
    root_logger.addHandler(stderr_handler)
    root_logger.setLevel(appl.config.get("LOG_LEVEL", "WARNING"))


def gunicorn_loggers(appl: Flask) -> None:
    """Logging with gunicorn WSGI server."""
    logger = logging.getLogger("gunicorn.error")
    appl.logger.handlers = logger.handlers
    appl.logger.setLevel(logger.level)

def setup_logging(appl: Flask) -> None:
    """Setup appropriate logging"""
    software, *_version_and_comments = os.environ.get(
        "SERVER_SOFTWARE", "").split('/')
    gunicorn_loggers(app) if software == "gunicorn" else dev_loggers(app)


app = Flask(__name__)
## BEGIN: Setup configurations ##
# See http://flask.pocoo.org/docs/config/#configuring-from-files
# Note no longer use the badly named WQFLASK_OVERRIDES (nyi)
app.config.from_object('gn2.default_settings')
app.config.from_envvar('GN2_SETTINGS')
app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
# BEGIN: SECRETS -- Should be the last of the settings to load
secrets_file = Path(app.config.get("GN2_SECRETS", "")).absolute()
if secrets_file.exists() and secrets_file.is_file():
    app.config.from_pyfile(str(secrets_file))
# END: SECRETS
## END: Setup configurations ##
setup_logging(app)
### DO NOT USE logging BEFORE THIS POINT!!!! ###

app.jinja_env.globals.update(
    undefined=jinja2.StrictUndefined,
    numify=formatting.numify,
    logged_in=user_logged_in,
    authserver_authorise_uri=authserver_authorise_uri,
    user_details=user_details,
    num_collections=numcoll,
    datetime=datetime)


# Registering blueprints
app.register_blueprint(gn_docs_blueprint, url_prefix="/gn_docs")
app.register_blueprint(glossary_blueprint, url_prefix="/glossary")
app.register_blueprint(references_blueprint, url_prefix="/references")
app.register_blueprint(links_blueprint, url_prefix="/links")
app.register_blueprint(policies_blueprint, url_prefix="/policies")
app.register_blueprint(environments_blueprint, url_prefix="/environments")
app.register_blueprint(facilities_blueprint, url_prefix="/facilities")
app.register_blueprint(blogs_blueprint, url_prefix="/blogs")
app.register_blueprint(news_blueprint, url_prefix="/news")
app.register_blueprint(xapian_syntax_blueprint, url_prefix="/search-syntax")
app.register_blueprint(jupyter_notebooks, url_prefix="/jupyter_notebooks")

app.register_blueprint(resource_management, url_prefix="/resource-management")
app.register_blueprint(metadata_edit, url_prefix="/datasets/")
app.register_blueprint(metadata,
                       url_prefix="/metadata/")
app.register_blueprint(group_management, url_prefix="/group-management")
app.register_blueprint(jobs_bp, url_prefix="/jobs")
app.register_blueprint(oauth2, url_prefix="/oauth2")

from gn2.wqflask.app_errors import register_error_handlers
register_error_handlers(app)

try:
    check_mandatory_configs(app)
except StartupError as serr:
    app.startup_error = serr
    app.register_blueprint(startup_errors, url_prefix="/")

server_session = Session(app)

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

@app.context_processor
def include_admin_role_class():
    return {'AdminRole': AdminRole}


@app.context_processor
def include_data_role_class():
    return {'DataRole': DataRole}
