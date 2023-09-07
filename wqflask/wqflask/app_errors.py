"""Handle errors at the application's top-level"""
from flask import flash, redirect, current_app, render_template
from authlib.integrations.base_client.errors import InvalidTokenError

from wqflask.oauth2 import session
from wqflask.decorators import AuthorisationError

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return render_template(
        "authorisation_error.html", error_type=type(exc).__name__, error=exc)

def handle_invalid_token_error(exc: InvalidTokenError):
    flash("An invalid session token was detected. "
          "You have been logged out of the system.",
          "alert-danger")
    session.clear_session_info()
    return redirect("/")

__handlers__ = {
    AuthorisationError: handle_authorisation_error,
    InvalidTokenError: handle_invalid_token_error
}

def register_error_handlers(app):
    """Register all error handlers."""
    for klass, handler in __handlers__.items():
        app.register_error_handler(klass, handler)

    return app
