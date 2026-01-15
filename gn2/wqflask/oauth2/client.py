"""Common oauth2 client utilities."""
import json
import time
import random
import logging
import requests
from typing import Optional
from functools import partial
from urllib.parse import urljoin
from datetime import datetime, timedelta

from flask import current_app as app
from pymonad.either import Left, Right, Either
from authlib.common.urls import url_decode
from authlib.jose.errors import BadSignatureError
from authlib.jose import KeySet, JsonWebKey, JsonWebToken
from authlib.integrations.requests_client import OAuth2Session

from gn2.debug import __pk__
from gn2.wqflask.oauth2 import session
from gn2.wqflask.external_errors import ExternalRequestError

logger = logging.getLogger(__name__)

SCOPE = ("profile group role resource user masquerade introspect")

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
    return suser["logged_in"] and suser["token"].is_right()


def __make_token_validator__(keys: KeySet):
    """Make a token validator function."""
    def __validator__(token: dict):
        for key in keys.keys:
            try:
                # Fixes CVE-2016-10555. See
                # https://docs.authlib.org/en/latest/jose/jwt.html
                jwt = JsonWebToken(["RS256"])
                jwt.decode(token["access_token"], key)
                return Right(token)
            except BadSignatureError:
                pass

        return Left("INVALID-TOKEN")

    return __validator__


def auth_server_jwks() -> Optional[KeySet]:
    """Fetch the auth-server JSON Web Keys information."""
    _jwks = session.session_info().get("auth_server_jwks")
    if bool(_jwks):
        return {
            "last-updated": _jwks["last-updated"],
            "jwks": KeySet([
                JsonWebKey.import_key(key) for key in _jwks.get(
                    "jwks", {"keys": []})["keys"]])}


def __validate_token__(keys):
    """Validate that the token is really from the auth server."""
    def __index__(_sess):
        return _sess
    return session.user_token().then(__make_token_validator__(keys)).then(
        session.set_user_token).either(__index__, __index__)


def __update_auth_server_jwks__():
    """Updates the JWKs every 2 hours or so."""
    jwks = auth_server_jwks()
    if bool(jwks):
        last_updated = jwks.get("last-updated")
        now = datetime.now().timestamp()
        if len(jwks["jwks"].keys) > 0 and bool(last_updated) and (now - last_updated) < timedelta(hours=2).seconds:
            return __validate_token__(jwks["jwks"])

    jwksuri = urljoin(authserver_uri(), "auth/public-jwks")
    jwks = KeySet([
        JsonWebKey.import_key(key)
        for key in requests.get(jwksuri).json()["jwks"]])
    session.set_auth_server_jwks(jwks)
    return __validate_token__(jwks)


def is_token_expired(token) -> bool:
    """Check whether the token has expired."""
    __update_auth_server_jwks__()
    jwks = auth_server_jwks()
    if bool(jwks):
        logger.debug("Got the keys from the auth server.")
        for jwk in jwks["jwks"].keys:
            try:
                jwt = JsonWebToken(["RS256"]).decode(
                    token["access_token"], key=jwk)
                return bool(jwt.get("exp")) and datetime.now().timestamp() > jwt["exp"]
            except BadSignatureError as _bse:
                pass

    logger.debug("Did not get keys from the auth server.")
    return True


def oauth2_client():
    def __update_token__(token, refresh_token=None, access_token=None):
        """Update the token when refreshed."""
        session.set_user_token(token)
        return token

    def __delay__():
        """Do a tiny delay."""
        time.sleep(random.choice(tuple(i/1000.0 for i in range(0,100))))

    def __json_auth__(client, method, uri, headers, body):
        return __pk__("AUTH ==> Sending …", (
            uri,
            {**headers, "Content-Type": "application/json"},
            json.dumps({
                **dict(url_decode(body)),
                "client_id": oauth2_clientid(),
                "client_secret": oauth2_clientsecret()
            })))

    def __client__(token) -> OAuth2Session:
        client = OAuth2Session(
            oauth2_clientid(),
            oauth2_clientsecret(),
            scope=(token["scope"] if token else SCOPE),
            token_endpoint=urljoin(authserver_uri(), "auth/token"),
            token_endpoint_auth_method="client_secret_post",
            token=token,
            update_token=__update_token__)
        client.register_client_auth_method(
            ("client_secret_post", __json_auth__))
        return client

    __update_auth_server_jwks__()
    return session.user_token().either(lambda _notok: __client__(None),
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

def oauth2_request(
        method: str,
        uri_path: str,
        data: dict = {},
        jsonify_p: bool = False,
        headers: dict = {"Content-Type": "application/json"},
        **kwargs
) -> Either:
    """Perform a HTTP request to the authorisation server."""
    assert method.lower() in (# 'connect' and 'trace' methods are not supported by requests.
        "get", "head", "post", "put", "delete", "options", "patch"), (
            "HTTP method '{method.upper()}' is not supported")
    resp = getattr(oauth2_client(), method.lower())(
        urljoin(authserver_uri(), uri_path),
        data=data,
        headers=headers,
        timeout=kwargs.get("timeout", (9.13, 20)),
        **{key: val for key,val in kwargs.items() if key != "timeout"}
    )
    if resp.status_code in range(200, 300):# mathematically [200, 299]
        return Right(resp.json() if resp.status_code != 204 else {})

    return Left(resp)

## Define utility function to avoid using `oauth2_request` function directly
oauth2_get = partial(oauth2_request, "get")
oauth2_head = partial(oauth2_request, "head")
oauth2_post = partial(oauth2_request, "post")
oauth2_put = partial(oauth2_request, "put")
oauth2_delete = partial(oauth2_request, "delete")
oauth2_options = partial(oauth2_request, "options")
oauth2_patch = partial(oauth2_request, "patch")

def no_token_get(
        uri_path: str,
        headers: dict = {"Content-Type": "application/json"},
        **kwargs
) -> Either:
    uri = urljoin(authserver_uri(), uri_path)
    try:
        resp = requests.get(
            uri,
            headers=headers,
            timeout=kwargs.get("timeout", (9.13, 20)),
            **{key: val for key,val in kwargs.items() if key != "timeout"})
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
        resp = requests.post(
            urljoin(authserver_uri(), uri_path),
            timeout=kwargs.get("timeout", (9.13, 20)),
            **{key: val for key,val in new_kwargs.items() if key != "timeout"})
        if resp.status_code == 200:
            return Right(resp.json())
        return Left(resp)
    except requests.exceptions.RequestException as exc:
        raise ExternalRequestError(uri_path, exc) from exc

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
