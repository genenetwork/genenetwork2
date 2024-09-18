"""Various checkers for OAuth2"""
from functools import wraps
from urllib.parse import urljoin

from flask import flash, request, redirect, url_for
from authlib.integrations.requests_client import OAuth2Session

from . import session
from .client import (
    oauth2_get,
    oauth2_client,
    authserver_uri,
    oauth2_clientid,
    oauth2_clientsecret)
from .request_utils import authserver_authorise_uri


def require_oauth2(func):
    """Decorator for ensuring user is logged in."""
    @wraps(func)
    def __token_valid__(*args, **kwargs):
        """Check that the user is logged in and their token is valid."""
        def __clear_session__(_no_token):
            session.clear_session_info()
            flash("You need to be logged in.", "alert-warning")
            return redirect("/")

        def __redirect_to_login__(_token):
            """
            Save the current user request to session then
            redirect to the login page.
            """
            if request.method == "GET":
                redirect_url = url_for(request.endpoint, **request.args)
            else:
                redirect_url = "/"
            session.set_redirect_url(redirect_url)
            return redirect(authserver_authorise_uri())

        def __with_token__(token):
            resp = oauth2_client().get(
                urljoin(authserver_uri(), "auth/user/"))
            user_details = resp.json()
            if not user_details.get("error", False):
                return func(*args, **kwargs)

            return __redirect_to_login__(token)

        return session.user_token().either(__redirect_to_login__, __with_token__)

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
