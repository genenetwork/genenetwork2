"""Entry point for flask app"""
# pylint: disable=C0413,E0611
import time
import jinja2

from flask import g
from flask import Flask
from typing import Tuple
from urllib.parse import urlparse
from utility import formatting
from wqflask.markdown_routes import glossary_blueprint
from wqflask.markdown_routes import references_blueprint
from wqflask.markdown_routes import links_blueprint
from wqflask.markdown_routes import policies_blueprint
from wqflask.markdown_routes import environments_blueprint
from wqflask.markdown_routes import facilities_blueprint
from wqflask.markdown_routes import blogs_blueprint

app = Flask(__name__)


# Helper function for getting the SQL objects
def parse_db_url(sql_uri: str) -> Tuple:
    """Parse SQL_URI env variable from an sql URI
    e.g. 'mysql://user:pass@host_name/db_name'

    """
    parsed_db = urlparse(sql_uri)
    return (parsed_db.hostname, parsed_db.username,
            parsed_db.password, parsed_db.path[1:])


# See http://flask.pocoo.org/docs/config/#configuring-from-files
# Note no longer use the badly named WQFLASK_OVERRIDES (nyi)
app.config.from_envvar('GN2_SETTINGS')

DB_HOST, DB_USER, DB_PASS, DB_NAME = parse_db_url(app.config.get('SQL_URI'))
app.config["DB_HOST"] = DB_HOST
app.config["DB_USER"] = DB_USER
app.config["DB_PASS"] = DB_PASS
app.config["DB_NAME"] = DB_NAME

app.jinja_env.globals.update(
    undefined=jinja2.StrictUndefined,
    numify=formatting.numify)

# Registering blueprints
app.register_blueprint(glossary_blueprint, url_prefix="/glossary")
app.register_blueprint(references_blueprint, url_prefix="/references")
app.register_blueprint(links_blueprint, url_prefix="/links")
app.register_blueprint(policies_blueprint, url_prefix="/policies")
app.register_blueprint(environments_blueprint, url_prefix="/environments")
app.register_blueprint(facilities_blueprint, url_prefix="/facilities")
app.register_blueprint(blogs_blueprint, url_prefix="/blogs")


@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)


from wqflask.api import router
from wqflask import group_manager
from wqflask import resource_manager
from wqflask import search_results
from wqflask import export_traits
from wqflask import gsearch
from wqflask import update_search_results
from wqflask import docs
from wqflask import news
from wqflask import db_info
from wqflask import user_login
from wqflask import user_session

import wqflask.views
