"""Various checkers for OAuth2"""
from functools import wraps
from urllib.parse import urljoin

from flask import flash, request, redirect, url_for
from authlib.integrations.requests_client import OAuth2Session
from werkzeug.routing import BuildError
from gn_libs.mysqldb import database_connection

from . import session
from .client import (
    oauth2_get,
    oauth2_post,
    oauth2_client,
    authserver_uri,
    oauth2_clientid,
    oauth2_clientsecret)
from .request_utils import authserver_authorise_uri


def fetch_case_attribute_privs(token: dict, sql_uri: str, inbredset_id: int) -> list:
    with database_connection(sql_uri) as conn, conn.cursor() as cursor:
        cursor.execute(
                "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                (inbredset_id,))
        species_id = cursor.fetchone()
        if not species_id:
            return []
        species_id = species_id[0]
        resource_id = oauth2_get(
            f"auth/resource/populations/resource-id/{species_id}/{inbredset_id}"
        ).either(
            lambda _: False,
            lambda val: val["resource-id"]
        )
        if not resource_id:
            return []
        return oauth2_post(
            f"auth/resource/authorisation",
            json={
                "resource-ids": [resource_id],
            },
            headers={
                "Authorization": f"Bearer {token}"},
            timeout=300
        ).either(
            lambda _: [],
            lambda resp: [
                priv["privilege_id"]
                for role in resp.get(resource_id, {}).get("roles", [])
                for priv in role.get("privileges", [])]
        )


def require_oauth2(func):
    """Decorator for ensuring user is logged in."""
    @wraps(func)
    def __token_valid__(*args, **kwargs):
        """Check that the user is logged in and their token is valid."""
        def __redirect_to_login__(_token):
            """
            Save the current user request to session then
            redirect to the login page.
            """
            try:
                redirect_url = url_for(request.endpoint, _method="GET", **request.args)
            except BuildError:
                redirect_url = "/"
            session.set_redirect_url(redirect_url)
            return redirect(authserver_authorise_uri())

        def __with_token__(token):
            return func(*args, **kwargs)

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
            ## TODO: @bonz There is no such endpoint on gn-auth
            ##       see also GN3 commit 86d0f55bf
            f"auth/resource/authorisation/{resource_name}"
        ).either(
            lambda _: {"roles": []},
            lambda val: val
        )
        if "group:resource:edit-resource" not in result.get("roles", []):
            return redirect(f"/datasets/{resource_name}")
        return func(*args, **kwargs)
    return __check_edit_access__
