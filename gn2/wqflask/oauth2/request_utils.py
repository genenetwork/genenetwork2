"""General request utilities"""
from typing import Optional, Callable
from urllib.parse import urljoin, urlparse
from requests.exceptions import JSONDecodeError

import simplejson
from flask import (
    flash, request, url_for, redirect, Response, render_template,
    current_app as app)

from authlib.integrations.base_client.errors import MissingTokenError

from gn2.wqflask.external_errors import ExternalRequestError

from . import session
from .client import (
    SCOPE, oauth2_get, authserver_uri, oauth2_clientid, oauth2_clientsecret)

def authserver_authorise_uri():
    req_baseurl = urlparse(request.base_url, scheme=request.scheme)
    host_uri = f"{req_baseurl.scheme}://{req_baseurl.netloc}/"
    return urljoin(
        authserver_uri(),
        "auth/authorise?response_type=code"
        f"&client_id={oauth2_clientid()}"
        f"&redirect_uri={urljoin(host_uri, 'oauth2/code')}")

def system_privileges():
    def __handle_error__(err):
        error = process_error(err)
        msg = (
            f"Error from AUTH Server:\n\nError:\t{error['error']}\n\n"
            f"{error['error-trace']}\nStatus Code:\t{error['status_code']}\n\n")
        app.logger.error(msg)
        return tuple()

    def __fetch_privilege_ids__(sys_roles):
        return tuple(
            privilege['privilege_id'] for role in sys_roles for privilege in role["privileges"])

    try:
        return oauth2_get("auth/system/roles").either(
            __handle_error__,
            lambda sys_roles: __fetch_privilege_ids__(sys_roles))
    except MissingTokenError as _mte:
        return tuple()
    except Exception as _exc:
        app.logger.error("General, unhandled exception.", exc_info=True)
        raise _exc from None


def user_details(fetch_remote: bool = False):
    def __handle_error__(err):
        error = process_error(err)
        msg = (
            f"Error from AUTH Server:\n\nError:\t{error['error']}\n\n"
            f"{error['error-trace']}\nStatus Code:\t{error['status_code']}\n\n")
        app.logger.error(msg)
        raise Exception(msg)

    if fetch_remote:
        return oauth2_get("auth/user/").either(__handle_error__,
                                               lambda usr_dets: usr_dets)
    return session.session_info()["user"]


def process_error(error: Response,
                  message: str=("Requested endpoint was not found on the API "
                                "server.")
                  ) -> dict:
    if error.status_code in range(400, 500):
        error_trace = "<No stack trace>"
        try:
            err = error.json()
            error_trace = err.get("error-trace", error_trace)
            # Handle the specific NotFoundError for group membership
            if "error-trace" in err and "User is not a member of any group" in err["error-trace"]:
                msg = "You are not currently a member of any group. Please contact an administrator."
            else:
                potential_keys = [
                    key for key in err.keys() if key.startswith("error") and
                    key not in ("error-trace",)]
                msg = f"{error.reason}"
                if potential_keys:
                    msg = " ; ".join([f"{err[k]}" for k in potential_keys])
        except simplejson.errors.JSONDecodeError as _jde:
            msg = message
        return {
            "error": error.reason,
            "error_message": msg,
            "error_description": msg,
            "status_code": error.status_code,
            "error-trace": error_trace
        }
    try:
        return {**error.json(), "status_code": error.status_code}
    except JSONDecodeError as exc:
        msg = f"Could not parse error record into JSON:\n\n{error.content}"
        return {
            "error": "ExternalRequestError",
            "error-url": error.url,
            "error_message": msg,
            "error_description": msg,
            "status_code": error.status_code,
            "error-trace": error.content
        }

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
                handler(error)
        if redirect_uri:
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
        error_description = (error.get("error_description")
                             or error.get("error-description")
                             or "Error!")
        flash(f"{error['status_code']} {error['error']}: "
              f"{error_description}",
              "alert-danger")
        return response
    return __err__

def with_flash_success(response) -> Callable:
    def __succ__(msg) -> Response:
        message = msg.get("message") or msg.get("description") or "Success!"
        flash(f"Success: {message}", "alert-success")
        return response
    return __succ__
