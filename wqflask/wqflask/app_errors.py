"""Handle errors at the application's top-level"""

from flask import current_app, render_template

from wqflask.decorators import AuthorisationError

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return render_template(
        "authorisation_error.html", error_type=type(exc).__name__, error=exc)
