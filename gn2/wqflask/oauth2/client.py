"""Common oauth2 client utilities."""
import uuid
import json
import requests
from typing import Any, Optional
from urllib.parse import urljoin

from flask import jsonify, current_app as app
from pymonad.maybe import Just, Maybe, Nothing
from pymonad.either import Left, Right, Either
from authlib.integrations.requests_client import OAuth2Session

from gn2.wqflask.oauth2 import session
from gn2.wqflask.external_errors import ExternalRequestError

SCOPE = ("profile group role resource register-client user masquerade "
         "introspect migrate-data")

def authserver_uri():
    """Return URI to authorisation server."""
    return app.config["AUTH_SERVER_URL"]

def oauth2_clientid():
    """Return the client id."""
    return app.config["OAUTH2_CLIENT_ID"]

def oauth2_clientsecret():
    """Return the client secret."""
    return app.config["OAUTH2_CLIENT_SECRET"]


def user_logged_in():
    """Check whether the user has logged in."""
    suser = session.session_info()["user"]
    if suser["logged_in"]:
        if session.expired():
            session.clear_session_info()
            return False
        return suser["token"].is_right()
    return False


def oauth2_client():
    def __client__(token) -> OAuth2Session:
        return OAuth2Session(
            oauth2_clientid(), oauth2_clientsecret(),
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
        client = OAuth2Session(
            oauth2_clientid(), oauth2_clientsecret(),
            token=token, scope=SCOPE)
        resp = client.get(
            urljoin(authserver_uri(), uri_path),
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
        client = OAuth2Session(
            oauth2_clientid(), oauth2_clientsecret(),
            token=token, scope=SCOPE)
        resp = client.post(
            urljoin(authserver_uri(), uri_path), data=data, json=json,
            **kwargs)
        if resp.status_code == 200:
            return Right(resp.json())

        return Left(resp)

    return session.user_token().either(__no_token__, __post__)

def no_token_get(uri_path: str, **kwargs) -> Either:
    uri = urljoin(authserver_uri(), uri_path)
    try:
        resp = requests.get(uri, **kwargs)
        if resp.status_code == 200:
            return Right(resp.json())
        return Left(resp)
    except requests.exceptions.RequestException as exc:
        raise ExternalRequestError(uri, exc) from exc

def no_token_post(uri_path: str, **kwargs) -> Either:
    data = kwargs.get("data", {})
    the_json = kwargs.get("json", {})
    request_data = {
        **data,
        **the_json,
        "client_id": oauth2_clientid(),
        "client_secret": oauth2_clientsecret()
    }
    new_kwargs = {
        **{
            key: value for key, value in kwargs.items()
            if key not in ("data", "json")
        },
        ("data" if bool(data) else "json"): request_data
    }
    try:
        resp = requests.post(urljoin(authserver_uri(), uri_path),
                             **new_kwargs)
        if resp.status_code == 200:
            return Right(resp.json())
        return Left(resp)
    except requests.exceptions.RequestException as exc:
        raise ExternalRequestError(uri, exc) from exc

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
