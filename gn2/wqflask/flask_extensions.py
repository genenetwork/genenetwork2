"""
Here we customise some of the functions in flask for our particular use case.
"""
import logging
from typing import Any

from gn_libs.privileges import resources
from flask import render_template as _render

from gn2.wqflask.oauth2 import client


logger = logging.getLogger(__name__)


def render_template(template, **context: Any) -> str:
    """Extend flask's `render_template` function."""
    return client.get(
        "auth/system/roles"
    ).then(
        lambda sys_roles: {
            **context,
            "systemprivileges": tuple(
                priv["privilege_id"] for role in sys_roles
                    for priv in role["privileges"])
        }
    ).then(
        lambda databag: {
            **databag,
            "can_view": resources.can_view(
                databag.get("resourceprivileges", tuple())
                + databag["systemprivileges"]),
            "can_edit": resources.can_edit(
                databag.get("resourceprivileges", tuple())
                + databag["systemprivileges"]),
            "can_delete": resources.can_delete(
                databag.get("resourceprivileges", tuple())
                + databag["systemprivileges"]),
            "can_batch_edit": resources.can_batch_edit(
                databag["systemprivileges"])
        }
    ).either(
        lambda error: with_flash_error(_render(template, **context)),
        lambda databag: _render(template, **databag)
    )
