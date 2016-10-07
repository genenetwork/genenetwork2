from __future__ import absolute_import, division, print_function

import sys
import jinja2

from flask import Flask
from utility import formatting

import logging
logger = logging.getLogger(__name__ )
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

app.config.from_object('cfg.default_settings')   # Get the defaults from cfg.default_settings
app.config.from_envvar('WQFLASK_SETTINGS')       # See http://flask.pocoo.org/docs/config/#configuring-from-files
# Note we also use WQFLASK_OVERRIDES

app.jinja_env.globals.update(
    undefined = jinja2.StrictUndefined,
    numify = formatting.numify
)

import wqflask.views
