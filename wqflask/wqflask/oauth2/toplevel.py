"""Authentication endpoints."""
import requests
from urllib.parse import urljoin

from authlib.integrations.base_client.errors import OAuthError
from flask import (
    flash, request, session, Blueprint, url_for, redirect, render_template,
    current_app as app)

from .client import oauth2_client
from .checks import require_oauth2, user_logged_in

toplevel = Blueprint("toplevel", __name__)




@toplevel.route("/register-client", methods=["GET", "POST"])
@require_oauth2
def register_client():
    """Register an OAuth2 client."""
    return "USER IS LOGGED IN AND SUCCESSFULLY ACCESSED THIS ENDPOINT!"
