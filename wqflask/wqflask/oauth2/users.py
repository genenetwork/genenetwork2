import requests
from urllib.parse import urljoin

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, url_for, redirect, Response, Blueprint,
    render_template, current_app as app)

from .checks import require_oauth2, user_logged_in
from .client import oauth2_get, oauth2_post, oauth2_client
from .request_utils import user_details, request_error, process_error

users = Blueprint("user", __name__)

@users.route("/profile", methods=["GET"])
@require_oauth2
def user_profile():
    __id__ = lambda the_val: the_val
    usr_dets = user_details()
    client = oauth2_client()
    def __render__(usr_dets, roles=[], **kwargs):
        return render_template(
            "oauth2/view-user.html", user_details=usr_dets, roles=roles,
            user_privileges = tuple(
                privilege["privilege_id"] for role in roles
                for privilege in role["privileges"]),
            **kwargs)

    def __migrate_user_data_error__(
            error, user_details, roles, group_join_request):
        flash(f"Data Migration: {error['error']}: {error['error_description']}",
              "alert-warning")
        return __render__(
            user_details, roles, group_join_request=group_join_request)

    def __migrate_user_data_success__(
            msg, user_details, roles, group_join_request):
        flash(f"Data Migration: {msg['description']}",
              "alert-success")
        return __render__(
            user_details, roles, group_join_request=group_join_request)

    def __migrate_user_data__(user_details, roles, group_join_request):
        return oauth2_post(
            f"oauth2/data/user/{user_details['user_id']}/migrate",
            data={
                "user_id": user_details["user_id"]
            }).either(
                lambda err: __migrate_user_data_error__(
                    process_error(err), user_details, roles,
                    group_join_request),
                lambda mig_suc_msg: __migrate_user_data_success__(
                    mig_suc_msg, user_details, roles, group_join_request))

    def __roles_success__(roles):
        if bool(usr_dets.get("group")):
            return __render__(usr_dets, roles)
        return oauth2_get("oauth2/user/group/join-request").either(
            lambda err: __render__(
                user_details, group_join_error=process_error(err)),
            lambda gjr: __render__(usr_dets, roles=roles, group_join_request=gjr))

    return oauth2_get("oauth2/user/roles").either(
        lambda err: __render__(usr_dets, role_error=process_error(err)),
        __roles_success__)

@users.route("/request-add-to-group", methods=["POST"])
@require_oauth2
def request_add_to_group() -> Response:
    """Request to be added to a group."""
    form = request.form
    group_id = form["group"]

    def __error__(error):
        err = process_error(error)
        flash(f"{err['error']}: {err['error_message']}", "alert-danger")
        return redirect(url_for("oauth2.user.user_profile"))

    def __success__(response):
        flash(f"{response['message']} (Response ID: {response['request_id']})",
              "alert-success")
        return redirect(url_for("oauth2.user.user_profile"))

    return oauth2_post(f"oauth2/group/requests/join/{group_id}",
                       data=form).either(__error__, __success__)

@users.route("/login", methods=["GET", "POST"])
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

@users.route("/logout", methods=["GET", "POST"])
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

@users.route("/register", methods=["GET", "POST"])
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
        return redirect(url_for("oauth2.user.register_user"))

    flash("Registration successful! Please login to continue.", "alert-success")
    return redirect(url_for("oauth2.user.login"))
