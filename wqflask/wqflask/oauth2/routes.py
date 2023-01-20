"""Routes for the OAuth2 auth system in GN3"""
import requests
from urllib.parse import urljoin

from pymonad.maybe import Just, Maybe, Nothing
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, url_for, redirect, Blueprint, render_template,
    current_app as app)

from .checks import require_oauth2, user_logged_in

oauth2 = Blueprint("oauth2", __name__)

def get_endpoint(uri_path: str) -> Maybe:
    token = session.get("oauth2_token", False)
    if token and not bool(session.get("user_details", False)):
        config = app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            token=token)
        resp = client.get(
            urljoin(config["GN_SERVER_URL"], uri_path))
        resp_json = resp.json()

        if resp_json.get("error") == "invalid_token":
            flash(resp_json["error_description"], "alert-danger")
            flash("You are now logged out.", "alert-info")
            session.pop("oauth2_token", None)
            return Nothing

        return Just(resp_json)

    return Nothing

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
    if user_logged_in():
        token = session.get("oauth2_token", False)
        config = app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            scope = "profile resource", token=token)
        resp = client.revoke_token(urljoin(config["GN_SERVER_URL"], "oauth2/revoke"))
        keys = tuple(key for key in session.keys() if not key.startswith("_"))
        for key in keys:
            session.pop(key, default=None)

    return redirect("/")

@oauth2.route("/register-user", methods=["GET", "POST"])
def register_user():
    if user_logged_in():
        next_endpoint=request.args.get("next", url_for("/"))
        flash(("You cannot register a new user while logged in. "
               "Please logout to register a new user."),
              "alert-danger")
        return redirect(next_endpoint)

    if request.method == "GET":
        return render_template("oauth2/register_user.html")

    config = app.config
    form = request.form
    response = requests.post(
        urljoin(config["GN_SERVER_URL"], "oauth2/register-user"),
        data = {
            "user_name": form.get("user_name"),
            "email": form.get("email_address"),
            "password": form.get("password"),
            "confirm_password": form.get("confirm_password")})
    results = response.json()
    if "error" in results:
        error_messages = tuple(
            f"{results['error']}: {msg.strip()}"
            for msg in results.get("error_description").split("::"))
        for message in error_messages:
            flash(message, "alert-danger")
        return redirect(url_for("oauth2.register_user"))

    flash("Registration successful! Please login to continue.", "alert-success")
    return redirect(url_for("oauth2.login"))

@oauth2.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"

@oauth2.route("/user-profile", methods=["GET"])
@require_oauth2
def user_profile():
    __id__ = lambda the_val: the_val
    user_details = session.get("user_details", False) or get_endpoint(
        "oauth2/user").maybe(False, __id__)
    roles = get_endpoint("oauth/user-roles").maybe([], __id__)
    resources = []
    return render_template(
        "oauth2/view-user.html", user_details=user_details, roles=roles,
        resources=resources)
