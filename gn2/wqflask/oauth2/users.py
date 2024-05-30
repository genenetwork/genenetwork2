import requests
from uuid import UUID
from urllib.parse import urljoin

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, url_for, redirect, Response, Blueprint,
    current_app as app)

from . import client
from . import session
from .ui import render_ui
from .checks import require_oauth2
from .client import (oauth2_get, oauth2_post, oauth2_client,
                     authserver_uri, user_logged_in)
from .request_utils import (
    user_details, request_error, process_error, with_flash_error)

users = Blueprint("user", __name__)

@users.route("/profile", methods=["GET"])
@require_oauth2
def user_profile():
    __id__ = lambda the_val: the_val
    usr_dets = user_details()
    def __render__(usr_dets, roles=[], **kwargs):
        return render_ui(
            "oauth2/view-user.html", user_details=usr_dets, roles=roles,
            user_privileges = tuple(
                privilege["privilege_id"] for role in roles
                for privilege in role["privileges"]),
            **kwargs)

    def __roles_success__(roles):
        if bool(usr_dets.get("group")):
            return __render__(usr_dets, roles)
        return oauth2_get("auth/user/group/join-request").either(
            lambda err: __render__(
                user_details, group_join_error=process_error(err)),
            lambda gjr: __render__(usr_dets, roles=roles, group_join_request=gjr))

    return oauth2_get("auth/system/roles").either(
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

    return oauth2_post(f"auth/group/requests/join/{group_id}",
                       data=form).either(__error__, __success__)


@users.route("/logout", methods=["GET", "POST"])
def logout():
    if user_logged_in():
        resp = oauth2_client().revoke_token(
            urljoin(authserver_uri(), "auth/revoke"))
        the_session = session.session_info()
        if not bool(the_session["masquerading"]):
            # Normal session - clear and go back.
            session.clear_session_info()
            flash("Successfully logged out.", "alert-success")
            return redirect("/")
        # Restore masquerading session
        session.unset_masquerading()
        flash(
            "Successfully logged out as user "
            f"{the_session['user']['name']} ({the_session['user']['email']}) "
            "and restored session for user "
            f"{the_session['masquerading']['name']} "
            f"({the_session['masquerading']['email']})",
            "alert-success")
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
        return render_ui("oauth2/register_user.html")

    form = request.form
    response = requests.post(
        urljoin(authserver_uri(), "auth/user/register"),
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
    return redirect("/")

@users.route("/masquerade", methods=["GET", "POST"])
def masquerade():
    """Masquerade as a particular user."""
    if request.method == "GET":
        this_user = session.session_info()["user"]
        return client.get("auth/user/list").either(
            lambda err: render_ui(
                "oauth2/masquerade.html", users_error=process_error(err)),
            lambda usrs: render_ui(
                "oauth2/masquerade.html", users=tuple(
                    usr for usr in usrs
                    if UUID(usr["user_id"]) != this_user["user_id"])))

    def __masq_success__(masq_details):
        session.set_masquerading(masq_details)
        flash(
            f"User {masq_details['original']['user']['name']} "
            f"({masq_details['original']['user']['email']}) is now "
            "successfully masquerading as the user "
            f"User {masq_details['masquerade_as']['user']['name']} "
            f"({masq_details['masquerade_as']['user']['email']}) is now ",
            "alert-success")
        return redirect("/")
    form = request.form
    masquerade_as = form.get("masquerade_as").strip()
    if not(bool(masquerade_as)):
        flash("You must provide a user to masquerade as.", "alert-danger")
        return redirect(url_for("oauth2.user.masquerade"))
    return client.post(
        "auth/user/masquerade/",
        json={"masquerade_as": request.form.get("masquerade_as")}).either(
            with_flash_error(redirect(url_for("oauth2.user.masquerade"))),
            __masq_success__)
