"""UI utilities"""
from flask import session, render_template

from .client import oauth2_get
from .client import user_logged_in
from .request_utils import process_error

def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    roles = kwargs.get("roles", tuple()) # Get roles
    user_privileges = tuple(
        privilege for role in roles for privilege in role["privileges"])
    kwargs = {
        **kwargs, "roles": roles, "user_privileges": user_privileges
    }
    return render_template(templatepath, **kwargs)
