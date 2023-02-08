"""General request utilities"""
from typing import Optional

from flask import (
    flash, session, url_for, redirect, Response, render_template,
    current_app as app)

from .client import oauth2_get

def raise_unimplemented():
    raise Exception("NOT IMPLEMENTED")

def user_details():
    return oauth2_get("oauth2/user").either(
        handle_error("oauth2.login"),
        lambda usr_dets: usr_dets)

def process_error(error: Response,
                  message: str=("Requested endpoint was not found on the API "
                                "server.")
                  ) -> dict:
    if error.status_code == 404:
        return {
            "error": "NotFoundError",
            "error_message": message,
            "error_description": message
        }
    return error.json()

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
