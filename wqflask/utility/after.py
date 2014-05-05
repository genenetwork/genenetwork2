from __future__ import print_function, division, absolute_import

"""
See: http://flask.pocoo.org/docs/patterns/deferredcallbacks/#deferred-callbacks

"""

from flask import g

from wqflask import app

def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f

@app.after_request
def call_after_request_callbacks(response):
    for callback in getattr(g, 'after_request_callbacks', ()):
        callback(response)
    return response
