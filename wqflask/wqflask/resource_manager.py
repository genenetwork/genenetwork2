import redis
import json




from typing import Dict








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
    admin_status = check_owner_or_admin(resource_id=resource_id)
