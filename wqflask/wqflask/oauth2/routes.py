"""Routes for the OAuth2 auth system in GN3"""
from urllib.parse import urljoin

from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, url_for, redirect, Blueprint, render_template,
    current_app as app)

from .checks import require_oauth2, user_logged_in

oauth2 = Blueprint("oauth2", __name__)

@oauth2.route("/login", methods=["GET", "POST"])
def login():
    """Route to allow users to sign up."""
    next_endpoint=request.args.get("next", False)

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
        if next_endpoint:
            return redirect(url_for(next_endpoint))
        return redirect("/")

    return render_template("oauth2/login.html", next_endpoint=next_endpoint)


@oauth2.route("/logout", methods=["GET", "POST"])
def logout():
    keys = tuple(key for key in session.keys() if not key.startswith("_"))
    for key in keys:
        session.pop(key, default=None)

    return redirect("/")

@oauth2.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"
