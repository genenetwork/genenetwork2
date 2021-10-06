"""A script for adding users to a specific group.

Example:

Assuming there are no groups and 'test@bonfacemunyoki.com' does not
exist in Redis:

.. code-block:: bash
   python group.py -g "editors" -m "test@bonfacemunyoki.com"

results in::

   Successfully created the group: 'editors'
   Data: '{"admins": [], "members": []}'

If 'me@bonfacemunyoki.com' exists in 'users' in Redis and we run:

.. code-block:: bash
   python group.py -g "editors" -m "me@bonfacemunyoki.com"

now results in::

   No new group was created.
   Updated Data: {'admins': [], 'members': ['me@bonfacemunyoki.com']}

"""

import argparse
import datetime
import redis
import json
import uuid

from typing import Dict, Optional, Set


def create_group_data(users: Dict, target_group: str,
                      members: Optional[str] = None,
                      admins: Optional[str] = None) -> Dict:
    """Return a dictionary that contains the following keys: "key",
    "field", and "value" that can be used in a redis hash as follows:
    HSET key field value

    Parameters:

    - `users`: a list of users for example:

    {'8ad942fe-490d-453e-bd37-56f252e41603':
    '{"email_address": "me@test.com",
      "full_name": "John Doe",
      "organization": "Genenetwork",
      "password": {"algorithm": "pbkdf2",
                   "hashfunc": "sha256",
                    "salt": "gJrd1HnPSSCmzB5veMPaVk2ozzDlS1Z7Ggcyl1+pciA=",
                    "iterations": 100000, "keylength": 32,
                    "created_timestamp": "2021-09-22T11:32:44.971912",
                    "password": "edcdaa60e84526c6"},
                    "user_id": "8ad942fe", "confirmed": 1,
                    "registration_info": {
                        "timestamp": "2021-09-22T11:32:45.028833",
                        "ip_address": "127.0.0.1",
                        "user_agent": "Mozilla/5.0"}}'}

    - `target_group`: the group name that will be stored inside the
      "groups" hash in Redis.

    - `members`: a comma-separated list of values that contain members
      of the `target_group` e.g. "me@test1.com, me@test2.com,
      me@test3.com"

    - `admins`: a comma-separated list of values that contain
      administrators of the `target_group` e.g. "me@test1.com,
      me@test2.com, me@test3.com"

    """
    # Emails
    _members: Set = set("".join(members.split()).split(",")
                        if members else [])
    _admins: Set = set("".join(admins.split()).split(",")
                       if admins else [])

    # Unique IDs
    member_ids: Set = set()
    admin_ids: Set = set()

    for user_id, user_details in users.items():
        _details = json.loads(user_details)
        if _details.get("email_address") in _members:
            member_ids.add(user_id)
        if _details.get("email_address") in _admins:
            admin_ids.add(user_id)

    timestamp: str = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
    return {"key": "groups",
            "field": str(uuid.uuid4()),
            "value": json.dumps({
                "name": target_group,
                "admins": list(admin_ids),
                "members": list(member_ids),
                "changed_timestamp": timestamp,
            })}


if __name__ == "__main__":
    # Initialising the parser CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--group-name",
                        help="This is the name of the GROUP mask")
    parser.add_argument("-m", "--members",
                        help="Members of the GROUP mask")
    parser.add_argument("-a", "--admins",
                        help="Admins of the GROUP mask")
    args = parser.parse_args()

    if not args.group_name:
        exit("\nExiting. Please specify a group name to use!\n")

    members = args.members if args.members else None
    admins = args.admins if args.admins else None

    REDIS_CONN = redis.Redis(decode_responses=True)
    USERS = REDIS_CONN.hgetall("users")

    if not any([members, admins]):
        exit("\nExiting. Please provide a value for "
             "MEMBERS(-m) or ADMINS(-a)!\n")

    data = create_group_data(
        users=USERS,
        target_group=args.group_name,
        members=members,
        admins=admins)

    if not REDIS_CONN.hget("groups", data.get("field")):
        updated_data = json.loads(data["value"])
        updated_data["created_timestamp"] = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        data["value"] = json.dumps(updated_data)

    created_p = REDIS_CONN.hset(data.get("key", ""),
                                data.get("field", ""),
                                data.get("value", ""))

    groups = json.loads(REDIS_CONN.hget("groups",
                                        args.group_name))  # type: ignore
    if created_p:
        exit(f"\nSuccessfully created the group: '{args.group_name}'\n"
             f"`HGETALL groups {args.group_name}`: {groups}\n")
    exit("\nNo new group was created.\n"
         f"`HGETALL groups {args.group_name}`: {groups}\n")
