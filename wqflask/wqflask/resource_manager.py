import redis
import json
import functools

from enum import Enum, unique



from typing import Dict


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
