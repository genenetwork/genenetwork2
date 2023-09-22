"""Common oauth2 client utilities."""
import json
import requests
from typing import Any, Optional
from urllib.parse import urljoin

from flask import jsonify, current_app as app
from pymonad.maybe import Just, Maybe, Nothing
from pymonad.either import Left, Right, Either
from authlib.integrations.requests_client import OAuth2Session

from wqflask.oauth2 import session
from wqflask.oauth2.checks import user_logged_in

SCOPE = ("profile group role resource register-client user masquerade "
         "introspect migrate-data")

def oauth2_client():
    def __client__(token) -> OAuth2Session:
        from utility.tools import (
            AUTH_SERVER_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
        return OAuth2Session(
            OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET,
            scope=SCOPE, token_endpoint_auth_method="client_secret_post",
            token=token)
    return session.user_token().either(
        lambda _notok: __client__(None),
        lambda token: __client__(token))

def __no_token__(_err) -> Left:
    """Handle situation where request is attempted with no token."""
    resp = requests.models.Response()
    resp._content = json.dumps({
        "error": "AuthenticationError",
        "error-description": ("You need to authenticate to access requested "
                              "information.")}).encode("utf-8")
    resp.status_code = 400
    return Left(resp)

def oauth2_get(uri_path: str, data: dict = {}, **kwargs) -> Either:
    def __get__(token) -> Either:
        from utility.tools import (
            AUTH_SERVER_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
        client = OAuth2Session(
            OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET,
            token=token, scope=SCOPE)
        resp = client.get(
            urljoin(AUTH_SERVER_URL, uri_path),
            data=data,
            **kwargs)
        if resp.status_code == 200:
            return Right(resp.json())

        return Left(resp)

    return session.user_token().either(__no_token__, __get__)

def oauth2_post(
        uri_path: str, data: Optional[dict] = None, json: Optional[dict] = None,
        **kwargs) -> Either:
    def __post__(token) -> Either:
        from utility.tools import (
            AUTH_SERVER_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
        client = OAuth2Session(
            OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET,
            token=token, scope=SCOPE)
        resp = client.post(
            urljoin(AUTH_SERVER_URL, uri_path), data=data, json=json,
            **kwargs)
        if resp.status_code == 200:
            return Right(resp.json())

        return Left(resp)

    return session.user_token().either(__no_token__, __post__)

def no_token_get(uri_path: str, **kwargs) -> Either:
    from utility.tools import AUTH_SERVER_URL
    resp = requests.get(urljoin(AUTH_SERVER_URL, uri_path), **kwargs)
    if resp.status_code == 200:
        return Right(resp.json())
    return Left(resp)

def no_token_post(uri_path: str, **kwargs) -> Either:
    from utility.tools import (
        AUTH_SERVER_URL, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
    data = kwargs.get("data", {})
    the_json = kwargs.get("json", {})
    request_data = {
        **data,
        **the_json,
        "client_id": OAUTH2_CLIENT_ID,
        "client_secret": OAUTH2_CLIENT_SECRET
    }
    new_kwargs = {
        **{
            key: value for key, value in kwargs.items()
            if key not in ("data", "json")
        },
        ("data" if bool(data) else "json"): request_data
    }
    resp = requests.post(urljoin(AUTH_SERVER_URL, uri_path),
                         **new_kwargs)
    if resp.status_code == 200:
        return Right(resp.json())
    return Left(resp)

def post(uri_path: str, **kwargs) -> Either:
    """
    Generic function to do POST requests, that checks whether or not the user is
    logged in and selects the appropriate function/method to run.
    """
    if user_logged_in():
        return oauth2_post(uri_path, **kwargs)
    return no_token_post(uri_path, **kwargs)

def get(uri_path: str, **kwargs) -> Either:
    """
    Generic function to do GET requests, that checks whether or not the user is
    logged in and selects the appropriate function/method to run.
    """
    if user_logged_in():
        return oauth2_get(uri_path, **kwargs)
    return no_token_get(uri_path, **kwargs)
