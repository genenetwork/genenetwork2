"""Various checkers for OAuth2"""
from functools import wraps
from urllib.parse import urljoin

from authlib.integrations.requests_client import OAuth2Session
from flask import (
    flash, request, redirect, session as flask_session)

from . import session
from .session import clear_session_info
from .client import (
    oauth2_get,
    oauth2_client,
    authserver_uri,
    oauth2_clientid,
    oauth2_clientsecret)


def require_oauth2(func):
    """Decorator for ensuring user is logged in."""
    @wraps(func)
    def __token_valid__(*args, **kwargs):
        """Check that the user is logged in and their token is valid."""

        def __clear_session__(_no_token):
            session.clear_session_info()
            flask_session.pop("oauth2_token", None)
            flask_session.pop("user_details", None)
            flash("You need to be logged in.", "alert-warning")
            return redirect("/")

        def __with_token__(token):
            resp = oauth2_client().get(
                urljoin(authserver_uri(), "auth/user/"))
            user_details = resp.json()
            if not user_details.get("error", False):
                return func(*args, **kwargs)

            return clear_session_info(token)

        return session.user_token().either(__clear_session__, __with_token__)

    return __token_valid__


def require_oauth2_edit_resource_access(func):
    """Check if a user has edit access for a given resource."""
    @wraps(func)
    def __check_edit_access__(*args, **kwargs):
        # Check edit access, if not return to the same page.

        # This is for a GET
        resource_name = request.args.get("name", "")
        # And for a POST request.
        if request.method == "POST":
            resource_name = request.form.get("name", "")
        result = oauth2_get(
            f"auth/resource/authorisation/{resource_name}"
        ).either(
            lambda _: {"roles": []},
            lambda val: val
        )
        if "group:resource:edit-resource" not in result.get("roles", []):
            return redirect(f"/datasets/{resource_name}")
        return func(*args, **kwargs)
    return __check_edit_access__
