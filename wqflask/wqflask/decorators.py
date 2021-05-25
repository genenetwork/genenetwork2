"""This module contains gn2 decorators"""
from flask import g
from functools import wraps


def admin_login_required(f):
    """Use this for endpoints where admins are required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.user_session.record.get(b"user_email_address") not in [
                b"labwilliams@gmail.com"]:
            return "You need to be admin", 401
        return f(*args, **kwargs)
    return wrap
