"""Routes for the OAuth2 auth system in GN3"""
import uuid
import requests
from typing import Optional
from urllib.parse import urljoin

from pymonad.maybe import Just, Maybe, Nothing
from pymonad.either import Left, Right, Either
from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, url_for, redirect, Blueprint, render_template,
    current_app as app)

from .checks import require_oauth2, user_logged_in

oauth2 = Blueprint("oauth2", __name__)
SCOPE = "profile group role resource register-client"

def __raise_unimplemented__():
    raise Exception("NOT IMPLEMENTED")

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

def __user_details__():
    return session.get("user_details", False) or get_endpoint(
        "oauth2/user").maybe(False, __id__)

def oauth2_get(uri_path: str) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.get(
            urljoin(config["GN_SERVER_URL"], uri_path))
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)

def oauth2_post(uri_path: str, data: dict) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.post(urljoin(config["GN_SERVER_URL"], uri_path), data=data)
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)

def __request_error__(response):
    app.logger.error(f"{response}: {response.url} [{response.status_code}]")
    return render_template("oauth2/request_error.html", response=response)

@oauth2.route("/login", methods=["GET", "POST"])
def login():
    """Route to allow users to sign up."""
    next_endpoint=request.args.get("next", False)

    if request.method == "POST":
        config = app.config
        form = request.form
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            scope=SCOPE, token_endpoint_auth_method="client_secret_post")
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


@oauth2.route("/logout", methods=["GET", "POST"])
def logout():
    if user_logged_in():
        token = session.get("oauth2_token", False)
        config = app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            scope = SCOPE, token=token)
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
    user_details = __user_details__()
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        scope = SCOPE, token=session.get("oauth2_token"))

    roles = oauth2_get("oauth2/user-roles").either(lambda x: "Error", lambda x: x)
    return render_template(
        "oauth2/view-user.html", user_details=user_details, roles=roles)

@oauth2.route("/request-add-to-group", methods=["POST"])
@require_oauth2
def request_add_to_group():
    return "WOULD SEND MESSAGE TO HAVE YOU ADDED TO GROUP..."

def __handle_error__(redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(error):
        print(f"ERROR: {error}")
        msg = error.get(
            "error_message", error.get("error_description", "undefined error"))
        flash(f"{error['error']}: {msg}.",
              "alert-danger")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__

def __handle_success__(
        success_msg: str, redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(response):
        flash(f"Success: {success_msg}.", "alert-success")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__

@oauth2.route("/create-group", methods=["POST"])
@require_oauth2
def create_group():
    def __setup_group__(response):
        session["user_details"]["group"] = response

    resp = oauth2_post("oauth2/create-group", data=dict(request.form))
    return resp.either(
        __handle_error__("oauth2.group_join_or_create"),
        __handle_success__(
            "Created group", "oauth2.user_profile",
            response_handlers=__setup_group__))

@oauth2.route("/group-join-or-create", methods=["GET"])
def group_join_or_create():
    user_details = __user_details__()
    if bool(user_details["group"]):
        flash("You are already a member of a group.", "alert info.")
        return redirect(url_for("oauth2.user_profile"))
    groups = oauth2_get("oauth2/groups").either(
        lambda x: __raise_unimplemented__(), lambda x: x)
    return render_template("oauth2/group_join_or_create.html", groups=groups)

@oauth2.route("/user-resources", methods=["GET"])
def user_resources():
    def __success__(resources):
        return render_template("oauth2/resources.html", resources=resources)

    return oauth2_get("oauth2/user-resources").either(
        __request_error__, __success__)

@oauth2.route("/user-roles", methods=["GET"])
def user_roles():
    def __success__(roles):
        return render_template("oauth2/list_roles.html", roles=roles)

    return oauth2_get("oauth2/user-roles").either(
        __request_error__, __success__)

@oauth2.route("/user-group", methods=["GET"])
def user_group():
    def __success__(group):
        return render_template("oauth2/group.html", group=group)

    return oauth2_get("oauth2/user-group").either(
        __request_error__, __success__)

@oauth2.route("/role/<uuid:role_id>", methods=["GET"])
def role(role_id: uuid.UUID):
    def __success__(the_role):
        return render_template("oauth2/role.html", role=the_role)

    return oauth2_get(f"oauth2/role/{role_id}").either(
        __request_error__, __success__)
