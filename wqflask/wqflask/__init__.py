import sys
import jinja2

from flask import Flask
from utility import formatting

import logging
logger = logging.getLogger(__name__ )
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

app.config.from_envvar('GN2_SETTINGS')       # See http://flask.pocoo.org/docs/config/#configuring-from-files
# Note no longer use the badly named WQFLASK_OVERRIDES (nyi)

app.jinja_env.globals.update(
    undefined = jinja2.StrictUndefined,
    numify = formatting.numify
)

from wqflask.api import router
import wqflask.views
