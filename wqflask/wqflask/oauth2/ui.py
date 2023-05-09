"""UI utilities"""
from flask import session, render_template

from .client import oauth2_get
from .request_utils import process_error

def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    logged_in = lambda: ("oauth2_token" in session and bool(session["oauth2_token"]))
    roles = kwargs.get("roles", tuple()) # Get roles if already provided
    if logged_in and not bool(roles): # If not, try fetching them
        roles_results = oauth2_get("oauth2/user/roles").either(
            lambda err: {"roles_error": process_error(err)},
            lambda roles: {"roles": roles})
        kwargs = {**kwargs, **roles_results}
        roles = kwargs.get("roles", tuple())
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles
        for privilege in role["privileges"])
    kwargs = {
        **kwargs, "roles": roles, "user_privileges": user_privileges,
        "logged_in": logged_in
    }
    return render_template(templatepath, **kwargs)
