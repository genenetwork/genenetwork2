"""Common oauth2 client utilities."""
from urllib.parse import urljoin

from flask import session, current_app as app
from pymonad.maybe import Just, Maybe, Nothing
from pymonad.either import Left, Right, Either
from authlib.integrations.requests_client import OAuth2Session

SCOPE = "profile group role resource register-client"

def oauth2_client():
    config = app.config
    return OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        scope=SCOPE, token_endpoint_auth_method="client_secret_post",
        token=session.get("oauth2_token"))

def get_endpoint(uri_path: str) -> Maybe:
    token = session.get("oauth2_token", False)
    if token and not bool(session.get("user_details", False)):
        config = app.config
        client = OAuth2Session(
            config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
            token=token)
        resp = client.get(
            urljoin(config["GN_SERVER_URL"], uri_path))
        resp_json = resp.json()

        if resp_json.get("error") == "invalid_token":
            flash(resp_json["error_description"], "alert-danger")
            flash("You are now logged out.", "alert-info")
            session.pop("oauth2_token", None)
            return Nothing

        return Just(resp_json)

    return Nothing

def oauth2_get(uri_path: str) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.get(
            urljoin(config["GN_SERVER_URL"], uri_path))
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)

def oauth2_post(uri_path: str, data: dict) -> Either:
    token = session.get("oauth2_token")
    config = app.config
    client = OAuth2Session(
        config["OAUTH2_CLIENT_ID"], config["OAUTH2_CLIENT_SECRET"],
        token=token, scope=SCOPE)
    resp = client.post(urljoin(config["GN_SERVER_URL"], uri_path), data=data)
    if resp.status_code == 200:
        return Right(resp.json())

    return Left(resp)
