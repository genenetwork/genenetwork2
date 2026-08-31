"""
Here we customise some of the functions in flask for our particular use case.
"""
import logging
from typing import Any

from gn_libs.privileges import resources
from flask import render_template as _render

from gn2.wqflask.oauth2 import client
from gn2.wqflask.oauth2.request_utils import with_flash_error

logger = logging.getLogger(__name__)


def render_template(template, **context: Any) -> str:
    """Extend flask's `render_template` function."""
    def __compute_authorisations__(databag):
        _rprivs = databag.get("resourceprivileges", tuple())
        _sprivs = databag.get("systemprivileges", tuple())
        return {
            **databag,
            "can_view": resources.can_view(_rprivs, _sprivs),
            "can_edit": resources.can_edit(_rprivs, _sprivs),
            "can_delete": resources.can_delete(_rprivs, _sprivs),
            "can_batch_edit": resources.can_batch_edit(_sprivs)
        }

    return client.get(
        "auth/resource/system/roles"
    ).then(
        lambda sys_roles: {
            **context,
            "systemprivileges": tuple(
                priv["privilege_id"] for role in sys_roles
                    for priv in role["privileges"])
        }
    ).then(
        __compute_authorisations__
    ).either(
        lambda error: with_flash_error(_render(template, **context)),
        lambda databag: _render(template, **databag)
    )
