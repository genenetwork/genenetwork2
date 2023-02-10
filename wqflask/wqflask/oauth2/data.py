"""Handle linking data to groups."""

from flask import Response, Blueprint, render_template

from .request_utils import process_error
from .client import oauth2_get, oauth2_post

data = Blueprint("data", __name__)

@data.route("/list")
def list_data():
    
    def __render__(**kwargs):
        roles = kwargs.get("roles", [])
        user_privileges = tuple(
                privilege["privilege_id"] for role in roles
                for privilege in role["privileges"])
        return render_template(
            "oauth2/data-list.html",
            groups=kwargs.get("groups", []),
            data_items=kwargs.get("data_items", []),
            user_privileges=kwargs.get("user_privileges",[]),
            **{key:val for key,val in kwargs.items()
               if key not in ("groups", "data_items", "user_privileges")})

    groups = oauth2_get("oauth2/group/list").either(
        lambda err: {"groups_error": process_error(err)},
        lambda grp: {"groups": grp})
    roles = oauth2_get("oauth2/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})
    data_items = {}

    return __render__(**{**groups, **roles, **data_items})
