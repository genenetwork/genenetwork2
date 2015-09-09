from __future__ import absolute_import, division, print_function

import sys
print("sys.path is:", sys.path)

import jinja2

from flask import Flask
from utility import formatting

app = Flask(__name__)

app.config.from_object('cfg.default_settings')   # Get the defaults from cfg.default_settings
app.config.from_envvar('WQFLASK_SETTINGS')       # See http://flask.pocoo.org/docs/config/#configuring-from-files

print("Current application configuration:", app.config)

app.jinja_env.globals.update(
    undefined = jinja2.StrictUndefined,
    numify = formatting.numify
)

import wqflask.views
