"""Authentication endpoints."""
import requests
from urllib.parse import urljoin

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, Blueprint, url_for, redirect, render_template,
    current_app as app)

from .client import oauth2_client
from .checks import require_oauth2, user_logged_in

toplevel = Blueprint("toplevel", __name__)

@toplevel.route("/login", methods=["GET", "POST"])
def login():
    """Route to allow users to sign up."""
    next_endpoint=request.args.get("next", False)

    if request.method == "POST":
        form = request.form
        client = oauth2_client()
        config = app.config
        try:
            token = client.fetch_token(
                urljoin(config["GN_SERVER_URL"], "oauth2/token"),
                username=form.get("email_address"),
                password=form.get("password"),
                grant_type="password")
            session["oauth2_token"] = token
        except OAuthError as _oaerr:
            flash(_oaerr.args[0], "alert-danger")
            return render_template(
                "oauth2/login.html", next_endpoint=next_endpoint,
                email=form.get("email_address"))

    if user_logged_in():
        if next_endpoint:
            return redirect(url_for(next_endpoint))
        return redirect("/")

    return render_template("oauth2/login.html", next_endpoint=next_endpoint)


@toplevel.route("/logout", methods=["GET", "POST"])
def logout():
    if user_logged_in():
        token = session.get("oauth2_token", False)
        config = app.config
        client = oauth2_client()
        resp = client.revoke_token(urljoin(config["GN_SERVER_URL"], "oauth2/revoke"))
        keys = tuple(key for key in session.keys() if not key.startswith("_"))
        for key in keys:
            session.pop(key, default=None)

    return redirect("/")

@toplevel.route("/register-user", methods=["GET", "POST"])
def register_user():
    if user_logged_in():
        next_endpoint=request.args.get("next", "/")
        flash(("You cannot register a new user while logged in. "
               "Please logout to register a new user."),
              "alert-danger")
        return redirect(next_endpoint)

    if request.method == "GET":
        return render_template("oauth2/register_user.html")

    config = app.config
    form = request.form
    response = requests.post(
        urljoin(config["GN_SERVER_URL"], "oauth2/user/register"),
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
        return redirect(url_for("oauth2.toplevel.register_user"))

    flash("Registration successful! Please login to continue.", "alert-success")
    return redirect(url_for("oauth2.toplevel.login"))

@toplevel.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"
