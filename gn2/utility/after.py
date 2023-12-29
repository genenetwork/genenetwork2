"""
See: http://flask.pocoo.org/docs/patterns/deferredcallbacks/#deferred-callbacks

"""

from flask import g

from gn2.wqflask import app


def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f
