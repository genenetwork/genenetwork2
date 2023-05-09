"""Common oauth2 client utilities."""
import requests
from typing import Any, Optional
from urllib.parse import urljoin

from flask import session, current_app as app
from pymonad.maybe import Just, Maybe, Nothing
from pymonad.either import Left, Right, Either
from authlib.integrations.requests_client import OAuth2Session

SCOPE = "profile group role resource register-client user introspect migrate-data"

def oauth2_client():
    config = app.config
    return OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        scope=SCOPE, token_endpoint_auth_method="client_secret_post",
        token=session.get("oauth2_token"))

def oauth2_get(uri_path: str, data: dict = {}, **kwargs) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.get(
        urljoin(config["GN_SERVER_URL"], uri_path),
        data=data,
        **kwargs)
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)

def oauth2_post(
        uri_path: str, data: Optional[dict] = None, json: Optional[dict] = None,
        **kwargs) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.post(
        urljoin(config["GN_SERVER_URL"], uri_path), data=data, json=json,
        **kwargs)
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)

def no_token_get(uri_path: str, **kwargs) -> Either:
    config = app.config
    resp = requests.get(urljoin(config["GN_SERVER_URL"], uri_path), **kwargs)
    if resp.status_code == 200:
        return Right(resp.json())
    return Left(resp)

def no_token_post(uri_path: str, data: dict[str, Any]) -> Either:
    config = app.config
    request_data = {
        **data,
        "client_id": config["OAUTH2_CLIENT_ID"],
        "client_secret": config["OAUTH2_CLIENT_SECRET"]
    }
    resp = requests.post(urljoin(config["GN_SERVER_URL"], uri_path),
                         data=request_data, json=request_data)
    if resp.status_code == 200:
        return Right(resp.json())
    return Left(resp)
