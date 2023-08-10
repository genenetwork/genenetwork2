"""Checks to do before the application is started."""
from typing import Tuple

from flask import Blueprint, current_app, render_template

class StartupError(Exception):
    """Base class for Application Check Errors."""

class MissingConfigurationError(StartupError):
    """Raised in case of a missing required setting."""

    def __init__(self, missing=Tuple[str, ...]):
        """Initialise the MissingConfigurationError object."""
        super().__init__("At least one required configuration is missing.")
        self.missing = missing

startup_errors = Blueprint("app_check_errors", __name__)
__MANDATORY_CONFIGURATIONS__ = (
    "SECRET_KEY",
    "REDIS_URL", # URI to Redis server
    "SQL_URI", # URI to MariaDB server
    "GN_SERVER_URL", # REST API Server
    "AUTH_SERVER_URL" # Auth(entic/oris)ation Server
)

def check_mandatory_configs(app):
    """Check that all mandatory configuration settings are defined."""
    missing = tuple(
        setting for setting in __MANDATORY_CONFIGURATIONS__
        if (setting not in app.config
            or app.config.get(setting) is None
            or app.config.get(setting).strip() == ""))
    if len(missing) > 0:
        print(missing)
        raise MissingConfigurationError(missing)

@startup_errors.route("/")
def error_index():
    """Display errors experienced at application startup"""
    return render_template(
        "startup_errors.html",
        error_type = type(current_app.startup_error).__name__,
        error_value = current_app.startup_error)
