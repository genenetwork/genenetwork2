"""Various checkers for OAuth2"""
from functools import wraps
from urllib.parse import urljoin

from authlib.integrations.requests_client import OAuth2Session
from flask import flash, request, session, url_for, redirect, current_app

def user_logged_in():
    """Check whether the user has logged in."""
    return bool(session.get("oauth2_token", False))

def require_oauth2(func):
    """Decorator for ensuring user is logged in."""
    @wraps(func)
    def __token_valid__(*args, **kwargs):
        """Check that the user is logged in and their token is valid."""
        if user_logged_in():
            config = current_app.config
            client = OAuth2Session(
                config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
                token=session["oauth2_token"])
            resp = client.get(
                urljoin(config["GN_SERVER_URL"], "oauth2/user"))
            user_details = resp.json()
            if not user_details.get("error", False):
                return func(*args, **kwargs)

            session.pop("oauth2_token", None)
            session.pop("user_details", None)

        flash("You need to be logged in.", "alert-warning")
        return redirect(url_for("oauth2.toplevel.login", next=request.endpoint))

    return __token_valid__
