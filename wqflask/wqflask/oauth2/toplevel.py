"""Authentication endpoints."""
from uuid import UUID
from urllib.parse import urljoin
from flask import (
    flash, request, Blueprint, url_for, redirect, render_template,
    current_app as app)

from . import session
from .client import SCOPE, no_token_post
from .checks import require_oauth2, user_logged_in
from .request_utils import user_details, process_error

toplevel = Blueprint("toplevel", __name__)

@toplevel.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"

@toplevel.route("/code", methods=["GET"])
def authorisation_code():
    """Use authorisation code to get token."""
    def __error__(error):
        flash(f"{error['error']}: {error['error_description']}",
              "alert-danger")
        return redirect("/")

    def __success__(token):
        session.set_user_token(token)
        udets = user_details()
        session.set_user_details({
            "user_id": UUID(udets["user_id"]),
            "name": udets["name"],
            "token": session.user_token(),
            "logged_in": True
        })
        return redirect(url_for("oauth2.user.user_profile"))

    code = request.args.get("code", "")
    if bool(code):
        request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "scope": SCOPE,
            "redirect_uri": urljoin(
                request.base_url,
                url_for("oauth2.toplevel.authorisation_code")),
            "client_id": app.config["OAUTH2_CLIENT_ID"]
        }
        return no_token_post(
            "oauth2/token", data=request_data).either(
                lambda err: __error__(process_error(err)), __success__)
    flash("AuthorisationError: No code was provided.", "alert-danger")
    return redirect("/")
