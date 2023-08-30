"""General request utilities"""
from typing import Optional, Callable
from urllib.parse import urljoin, urlparse

import simplejson
from flask import (
    flash, request, url_for, redirect, Response, render_template,
    current_app as app)

from .client import SCOPE, oauth2_get

def authserver_authorise_uri():
    from utility.tools import AUTH_SERVER_URL, OAUTH2_CLIENT_ID
    req_baseurl = urlparse(request.base_url, scheme=request.scheme)
    host_uri = f"{req_baseurl.scheme}://{req_baseurl.netloc}/"
    return urljoin(
        AUTH_SERVER_URL,
        "/auth/authorise?response_type=code"
        f"&client_id={OAUTH2_CLIENT_ID}"
        f"&redirect_uri={urljoin(host_uri, 'oauth2/code')}")

def raise_unimplemented():
    raise Exception("NOT IMPLEMENTED")

def user_details():
    return oauth2_get("auth/user/").either(
        lambda err: {},
        lambda usr_dets: usr_dets)

def process_error(error: Response,
                  message: str=("Requested endpoint was not found on the API "
                                "server.")
                  ) -> dict:
    if error.status_code in range(400, 500):
        try:
            err = error.json()
            msg = err.get("error_description", f"{error.reason}")
        except simplejson.errors.JSONDecodeError as _jde:
            msg = message
        return {
            "error": error.reason,
            "error_message": msg,
            "error_description": msg,
            "status_code": error.status_code
        }
    return {**error.json(), "status_code": error.status_code}

def request_error(response):
    app.logger.error(f"{response}: {response.url} [{response.status_code}]")
    return render_template("oauth2/request_error.html", response=response)

def handle_error(redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(error):
        error_json = process_error(error)# error.json()
        msg = error_json.get(
            "error_message", error_json.get(
                "error_description", "undefined error"))
        flash(f"{error_json['error']}: {msg}.",
              "alert-danger")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__

def handle_success(
        success_msg: str, redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(response):
        flash(f"Success: {success_msg}.", "alert-success")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__

def flash_error(error):
    flash(f"{error['error']}: {error['error_description']}", "alert-danger")

def flash_success(success):
    flash(f"{success['description']}", "alert-success")

def with_flash_error(response) -> Callable:
    def __err__(err) -> Response:
        error = process_error(err)
        flash(f"{error['status_code']} {error['error']}: "
              f"{error['error_description']}",
              "alert-danger")
        return response
    return __err__

def with_flash_success(response) -> Callable:
    def __succ__(msg) -> Response:
        flash(f"Success: {msg['message']}", "alert-success")
        return response
    return __succ__
