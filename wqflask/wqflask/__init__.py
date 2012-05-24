from __future__ import absolute_import, division, print_function

from flask import Flask

from utility import formatting

app = Flask(__name__)

app.jinja_env.globals.update(
    numify = formatting.numify
)

import wqflask.views
