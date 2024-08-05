"""Handle errors at the application's top-level"""
import os
import random
import datetime
import traceback
from uuid import uuid4

from werkzeug.exceptions import InternalServerError
from authlib.integrations.base_client.errors import (
    OAuthError, InvalidTokenError)
from flask import (
    flash, request, redirect, current_app, render_template, make_response)

from gn2.wqflask.oauth2 import session
from gn2.wqflask.decorators import AuthorisationError
from gn2.wqflask.external_errors import ExternalRequestError

def render_error(exc):
    """Render the errors consistently."""
    error_desc = str(exc)
    time_str = datetime.datetime.utcnow().strftime('%l:%M%p UTC %b %d, %Y')
    formatted_lines = f"{request.url} ({time_str}) \n{traceback.format_exc()}"

    current_app.logger.error("(error-id: %s): %s\n\n%s",
                             exc.errorid if hasattr(exc, "errorid") else uuid4(),
                             error_desc,
                             formatted_lines)

    animation = request.cookies.get(error_desc[:32])
    if not animation:
        animation = random.choice([fn for fn in os.listdir(
            "./gn2/wqflask/static/gif/error") if fn.endswith(".gif")])

    resp = make_response(render_template(
        "error.html",
        message=error_desc,
        stack={formatted_lines},
        error_image=animation,
        version=current_app.config.get("GN_VERSION")))
    resp.set_cookie(error_desc[:32], animation)
    return resp

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return render_template(
        "authorisation_error.html", error_type=type(exc).__name__, error=exc)

def handle_invalid_token_error(exc: InvalidTokenError):
    """Handle InvalidTokenError"""
    flash("An invalid session token was detected. "
          "You have been logged out of the system.",
          "alert-danger")
    current_app.logger.error("Invalid token detected. %s", request.url, exc_info=True)
    session.clear_session_info()
    return redirect("/")

def __build_message__(exc: OAuthError) -> str:
    """Build up the message to flash for any OAuthError"""
    match exc.args[0]:
        case "ForbiddenAccess: Token does not belong to client.":
            return "An invalid token was used. The session has been cleared."
        case "ForbiddenAccess: Token is expired.":
            return "The session has expired."
        case "ForbiddenAccess: Token has previously been revoked.":
            return "Revoked token was used. The session has been cleared."
        case _:
            return exc.args[0]

def handle_oauth_error(exc: OAuthError):
    """Handle generic OAuthError"""
    flash((f"{type(exc).__name__}: {__build_message__(exc)} "
           "Please log in again to continue."),
          "alert-danger")
    current_app.logger.error("Invalid token detected. %s", request.url, exc_info=True)
    session.clear_session_info()
    return redirect("/")

__handlers__ = {
    OAuthError: handle_oauth_error,
    AuthorisationError: handle_authorisation_error,
    ExternalRequestError: lambda exc: render_error(exc),
    InternalServerError: lambda exc: render_error(exc),
    InvalidTokenError: handle_invalid_token_error
}

def register_error_handlers(app):
    """Register all error handlers."""
    for klass, handler in __handlers__.items():
        app.register_error_handler(klass, handler)

    return app
