"""UI utilities"""
from flask import session, render_template

from .client import oauth2_get
from .checks import user_logged_in
from .request_utils import process_error

def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    roles = kwargs.get("roles", tuple()) # Get roles if already provided
    if user_logged_in() and not bool(roles): # If not, try fetching them
        roles_results = oauth2_get("auth/system/roles").either(
            lambda err: {"roles_error": process_error(err)},
            lambda roles: {"roles": roles})
        kwargs = {**kwargs, **roles_results}
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles
        for privilege in role["privileges"])
    kwargs = {
        **kwargs, "roles": roles, "user_privileges": user_privileges
    }
    return render_template(templatepath, **kwargs)
