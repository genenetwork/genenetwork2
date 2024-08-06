"""UI utilities"""
from flask import session, render_template

from gn2.wqflask.oauth2 import session

from .client import oauth2_get
from .client import user_logged_in
from .request_utils import process_error

def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    roles = kwargs.get("roles", tuple()) # Get roles
    if not roles:
        roles = oauth2_get("auth/system/roles").either(
                lambda _err: roles, lambda auth_roles: auth_roles)
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles for privilege in role["privileges"])
    user_token = session.user_token().either(lambda _err: "", lambda token: token["access_token"])
    kwargs = {
            **kwargs, "roles": roles, "user_privileges": user_privileges, "bearer_token": user_token
    }
    return render_template(templatepath, **kwargs)
