"""UI utilities"""
from flask import render_template

from .client import oauth2_get


_USER_ADMIN_PRIVILEGES_ = (
    "system:user:edit",
    "system:user:list",
    "system:user:masquerade",
    "system:user:delete-user",
    "system:user:reset-password",
    "system:user:assign-group-leader")

_GROUP_ADMIN_PRIVILEGES_ = (
    "system:group:edit-group",
    "system:group:view-group",
    "system:group:create-group",
    "system:group:delete-group",
    "system:group:transfer-group-leader")


def __display_p__(actual: tuple[str, ...], check_for: tuple[str, ...]) -> bool:
    """Check that all elements in `check_for` exist in `actual`."""
    return all((priv in actual) for priv in check_for)


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
                "list_users": __display_p__(
                    _privilege_ids, _USER_ADMIN_PRIVILEGES_),
                "list_groups": __display_p__(
                    _privilege_ids, _GROUP_ADMIN_PRIVILEGES_)
            }
        })
