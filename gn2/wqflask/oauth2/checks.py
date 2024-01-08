"""Various checkers for OAuth2"""
from functools import wraps
from urllib.parse import urljoin

from authlib.integrations.requests_client import OAuth2Session
from flask import (
    flash, request, url_for, redirect, current_app, session as flask_session)

from . import session

def user_logged_in():
    """Check whether the user has logged in."""
    suser = session.session_info()["user"]
    if suser["logged_in"]:
        if session.expired():
            session.clear_session_info()
            return False
        return suser["token"].is_right()
    return False

def require_oauth2(func):
    """Decorator for ensuring user is logged in."""
    @wraps(func)
    def __token_valid__(*args, **kwargs):
        """Check that the user is logged in and their token is valid."""
        config = current_app.config
        def __clear_session__(_no_token):
            session.clear_session_info()
            flask_session.pop("oauth2_token", None)
            flask_session.pop("user_details", None)
            flash("You need to be logged in.", "alert-warning")
            return redirect("/")

        def __with_token__(token):
            from gn2.utility.tools import (
                AUTH_SERVER_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
            client = OAuth2Session(
                OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, token=token)
            resp = client.get(
                urljoin(AUTH_SERVER_URL, "auth/user/"))
            user_details = resp.json()
            if not user_details.get("error", False):
                return func(*args, **kwargs)

            return clear_session_info(token)

        return session.user_token().either(__clear_session__, __with_token__)

    return __token_valid__