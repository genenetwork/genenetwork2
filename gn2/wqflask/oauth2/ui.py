"""UI utilities"""
from flask import render_template

from .client import oauth2_get

def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    roles = kwargs.get("roles", tuple()) # Get roles
    if not roles:
        roles = oauth2_get("auth/system/roles").either(
                lambda _err: roles, lambda auth_roles: auth_roles)
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles for privilege in role["privileges"])
    kwargs = {
            **kwargs, "roles": roles, "user_privileges": user_privileges,
    }
    return render_template(templatepath, **kwargs)
