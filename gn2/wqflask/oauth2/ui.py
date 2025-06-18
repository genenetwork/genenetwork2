"""UI utilities"""
from flask import render_template

from .client import oauth2_get


def __display_list_users__(privileges):
    return all((priv in privileges)
               for priv in (
                       # "system:user:edit",
                       "system:user:list",
                       "system:user:masquerade",
                       "system:user:delete-user",
                       "system:user:reset-password",
                       "system:user:assign-group-leader"))


def render_ui(templatepath: str, **kwargs):
    """Handle repetitive UI rendering stuff."""
    roles = kwargs.get("roles", tuple()) # Get roles
    if not roles:
        roles = oauth2_get("auth/system/roles").either(
                lambda _err: roles, lambda auth_roles: auth_roles)
    user_privileges = tuple(
        privilege for role in roles for privilege in role["privileges"])
    _privilege_ids = tuple(priv["privilege_id"] for priv in user_privileges)
    return render_template(
        templatepath,
        **{
            **kwargs,
            "roles": roles,
            "user_privileges": user_privileges,
            "display": {
                "list_users": __display_list_users__(_privilege_ids)
            }
        })
