"""UI utilities"""
import logging

from flask import render_template
from gn_libs.privileges import system

from .client import oauth2_get

logger = logging.getLogger(__name__)


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
    return oauth2_get(
        f"auth/resource/system/roles"
    ).then(
        lambda sysroles: {
            "user_system_roles": sysroles,
            "user_privileges_on_system": tuple(
                privilege["privilege_id"]
                        for role in sysroles
                        for privilege in role.get("privileges", []))
        }
    ).then(
        lambda databag: {
            **databag,
            "sysauth": {
                "can_masquerade": system.can_masquerade(
                    databag["user_privileges_on_system"]),
                "can_link_data": system.can_link_data(
                    databag["user_privileges_on_system"])
            }
        }
    ).then(
        lambda databag: {
            **databag,
            "display": {
                "list_users": __display_p__(
                    databag["user_privileges_on_system"],
                    _USER_ADMIN_PRIVILEGES_),
                "list_groups": __display_p__(
                    databag["user_privileges_on_system"],
                    _GROUP_ADMIN_PRIVILEGES_)
            }
        }
    ).either(
        lambda err: render_template(templatepath,
                                    error=process_error(err)),
        lambda databag: render_template(templatepath,
                                        **{
                                            **kwargs,
                                            **databag
                                        })
    )
