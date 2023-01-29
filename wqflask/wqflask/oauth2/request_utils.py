"""General request utilities"""
from typing import Optional

from flask import (
    session, url_for, redirect, render_template, current_app as app)

def __raise_unimplemented__():
    raise Exception("NOT IMPLEMENTED")

def __user_details__():
    return session.get("user_details", False) or get_endpoint(
        "oauth2/user").maybe(False, __id__)

def __request_error__(response):
    app.logger.error(f"{response}: {response.url} [{response.status_code}]")
    return render_template("oauth2/request_error.html", response=response)


def __handle_error__(redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(error):
        print(f"ERROR: {error}")
        msg = error.get(
            "error_message", error.get("error_description", "undefined error"))
        flash(f"{error['error']}: {msg}.",
              "alert-danger")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__

def __handle_success__(
        success_msg: str, redirect_uri: Optional[str] = None, **kwargs):
    def __handler__(response):
        flash(f"Success: {success_msg}.", "alert-success")
        if "response_handlers" in kwargs:
            for handler in kwargs["response_handlers"]:
                handler(response)
        if redirect:
            return redirect(url_for(redirect_uri, **kwargs))

    return __handler__
