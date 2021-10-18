import redis
import json
import functools

from enum import Enum, unique

from flask import Blueprint
from flask import current_app
from flask import g
from flask import render_template

from typing import Dict

from wqflask.decorators import login_required


@functools.total_ordering
class OrderedEnum(Enum):
    @classmethod
    @functools.lru_cache(None)
    def _member_list(cls):
        return list(cls)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            member_list = self.__class__._member_list()
            return member_list.index(self) < member_list.index(other)
        return NotImplemented


@unique
class DataRole(OrderedEnum):
    NO_ACCESS = "no-access"
    VIEW = "view"
    EDIT = "edit"


@unique
class AdminRole(OrderedEnum):
    NOT_ADMIN = "not-admin"
    EDIT_ACCESS = "edit-access"
    EDIT_ADMINS = "edit-admins"


resource_management = Blueprint('resource_management', __name__)


def get_user_membership(conn: redis.Redis, user_id: str,
                        group_id: str) -> Dict:
    """Return a dictionary that indicates whether the `user_id` is a
    member or admin of `group_id`.

    Args:
      - conn: a Redis Connection with the responses decoded.
      - user_id: a user's unique id
        e.g. '8ad942fe-490d-453e-bd37-56f252e41603'
      - group_id: a group's unique id
      e.g. '7fa95d07-0e2d-4bc5-b47c-448fdc1260b2'

    Returns:
      A dict indicating whether the user is an admin or a member of
      the group: {"member": True, "admin": False}

    """
    results = {"member": False, "admin": False}
    for key, value in conn.hgetall('groups').items():
        if key == group_id:
            group_info = json.loads(value)
            if user_id in group_info.get("admins"):
                results["admin"] = True
            if user_id in group_info.get("members"):
                results["member"] = True
            break
    return results


def get_user_access_roles(conn: redis.Redis,
                          resource_info: Dict,
                          user_id: str) -> Dict:
    """Get the highest access roles for a given user

    Args:
      - conn: A redis connection with the responses decoded.
      - resource_info: A dict containing details(metadata) about a
        given resource.
      - user_id: The unique id of a given user.

    Returns:
      A dict indicating the highest access role the user has.

    """
    # This is the default access role
    access_role = {
        "data": [DataRole.NO_ACCESS],
        "metadata": [DataRole.NO_ACCESS],
        "admin": [AdminRole.NOT_ADMIN],
    }

    # Check the resource's default mask
    if default_mask := resource_info.get("default_mask"):
        access_role["data"].append(DataRole(default_mask.get("data")))
        access_role["metadata"].append(DataRole(default_mask.get("metadata")))
        access_role["admin"].append(AdminRole(default_mask.get("admin")))

    # Then check if the user is the owner Check with Zach and Rob if
    # the owner, be default should, as the lowest access_roles, edit
    # access
    if resource_info.get("owner_id") == user_id:
        access_role["data"].append(DataRole.EDIT)
        access_role["metadata"].append(DataRole.EDIT)
        access_role["admin"].append(AdminRole.EDIT_ACCESS)

    # Check the group mask. If the user is in that group mask, use the
    # access roles for that group
    if group_masks := resource_info.get("group_masks"):
        for group_id, roles in group_masks.items():
            user_membership = get_user_membership(conn=conn,
                                                  user_id=user_id,
                                                  group_id=group_id)
            if any(user_membership.values()):
                access_role["data"].append(DataRole(roles.get("data")))
                access_role["metadata"].append(
                    DataRole(roles.get("metadata")))
    return {k: max(v) for k, v in access_role.items()}


def add_extra_resource_metadata(conn: redis.Redis, resource: Dict) -> Dict:
    """If resource['owner_id'] exists, add metadata about that user. Also,
if the resource contains group masks, add the group name into the
resource dict. Note that resource['owner_id'] and the group masks are
unique identifiers so they aren't human readable names.

    Args:
      - conn: A redis connection with the responses decoded.
      - resource: A dict containing details(metadata) about a
        given resource.

    Returns:
      An embellished dictionary with the human readable names of the
    group masks and the owner id if it was set.

    """
    # Embellish the resource information with owner details if the
    # owner is set
    if (owner_id := resource.get("owner_id", "none").lower()) == "none":
        resource["owner_id"] = None
        resource["owner_details"] = None
    else:
        user_details = json.loads(conn.hget("users", owner_id))
        resource["owner_details"] = {
            "email_address": user_details.get("email_address"),
            "full_name": user_details.get("full_name"),
            "organization": user_details.get("organization"),
        }

    # Embellish the resources information with the group name if the
    # group masks are present
    if groups := resource.get('group_masks', {}):
        for group_id in groups.keys():
            resource['group_masks'][group_id]["group_name"] = (
                json.loads(conn.hget("groups", group_id)).get('name'))
    return resource


@resource_management.route("/resources/<resource_id>")
@login_required
def manage_resource(resource_id: str):
    user_id = (g.user_session.record.get(b"user_id",
                                         b"").decode("utf-8") or
               g.user_session.record.get("user_id", ""))
    redis_conn = redis.from_url(
        current_app.config["REDIS_URL"],
        decode_responses=True)

    # Abort early if the resource can't be found
    if not (resource := redis_conn.hget("resources", resource_id)):
        return f"Resource: {resource_id} Not Found!", 401

    return render_template(
        "admin/manage_resource.html",
        resource_info=(embellished_resource:=add_extra_resource_metadata(
            conn=redis_conn,
            resource=json.loads(resource))),
        access_role=get_user_access_roles(
            conn=redis_conn,
            resource_info=embellished_resource,
            user_id=user_id),
        DataRole=DataRole, AdminRole=AdminRole)
