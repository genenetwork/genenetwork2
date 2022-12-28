"""Routes for the OAuth2 auth system in GN3"""
import uuid
from urllib.parse import urljoin

import redis
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, redirect, Blueprint, render_template,
    current_app as app)

oauth2 = Blueprint("oauth2", __name__)

def user_logged_in():
    """Check whether the user has logged in."""
    return bool(session.get("oauth2_token", False))

@oauth2.route("/login", methods=["GET", "POST"])
def login():
    """Route to allow users to sign up."""
    if request.method == "POST":
        config = app.config
        form = request.form
        scope = "profile resource"
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            scope=scope, token_endpoint_auth_method="client_secret_post")
        try:
            token = client.fetch_token(
                urljoin(config["GN_SERVER_URL"], "oauth2/token"),
                username=form.get("email_address"),
                password=form.get("password"),
                grant_type="password")
            session["oauth2_token"] = token
        except OAuthError as _oaerr:
            flash(_oaerr.args[0], "alert-danger")
            return render_template("oauth2/login.html")

    if user_logged_in():
        return redirect("/")

    return render_template("oauth2/login.html")


@oauth2.route("/logout", methods=["GET", "POST"])
def logout():
    keys = tuple(key for key in session.keys() if not key.startswith("_"))
    for key in keys:
        session.pop(key, default=None)

    return redirect("/")
