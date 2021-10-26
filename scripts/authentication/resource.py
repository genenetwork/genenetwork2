#!/usr/bin/env python3
"""A script that:

- Optionally restores data from a json file.

- By default, without any args provided, adds the group: 'editors' to
every resource. 'editors' should have the right to edit both metadata
and data.

- Optionally creates a back-up every time you edit a resource.


To restore a back-up:

.. code-block:: python
   python resource.py --restore <PATH/TO/RESOURCE/BACK-UP/FILE>

To add editors to every resource without creating a back-up:

.. code-block:: python
   python resource.py

To add editors to every resource while creating a back-up before any
destructive edits:

.. code-block:: python
   python resource.py --enable-backup

"""
import argparse
import json
import redis
import os

from datetime import datetime


def recover_hash(name: str, file_path: str, set_function) -> bool:
    """Recover back-ups using the `set_function`

    Args:
      - name: Redis hash where `file_path` will be restored
      - file_path: File path where redis hash is sourced from
      - set_function: Function used to do the Redis backup for
        example: HSET

    Returns:
      A boolean indicating whether the function ran successfully.

    """
    try:
        with open(file_path, "r") as f:
            resources = json.load(f)
            for resource_id, resource in resources.items():
                set_function(name=name,
                             key=resource_id,
                             value=resource)
            return True
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":
    # Initialising the parser CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-id",
                        help="Add the group id to all resources")
    parser.add_argument("--restore",
                        help="Restore from a given backup")
    parser.add_argument("--enable-backup", action="store_true",
                        help="Create a back up before edits")
    args = parser.parse_args()

    if not args.group_id:
        exit("Please specify the group-id!\n")
    if args.restore:
        if recover_hash(name="resources",
                        file_path=args.back_up,
                        set_function=redis.Redis(decode_responses=True).hset):
            exit(f"\n Done restoring {args.back_up}!\n")
        else:
            exit(f"\n There was an error restoring {args.back_up}!\n")

    REDIS_CONN = redis.Redis(decode_responses=True)
    RESOURCES = REDIS_CONN.hgetall("resources")
    BACKUP_DIR = os.path.join(os.getenv("HOME"), "redis")
    if args.enable_backup:
        FILENAME = ("resources-"
                    f"{datetime.now().strftime('%Y-%m-%d-%I:%M:%S-%p')}"
                    ".json")
        if not os.path.exists(BACKUP_DIR):
            os.mkdir(BACKUP_DIR)
        with open(os.path.join(BACKUP_DIR, FILENAME), "w") as f:
            json.dump(RESOURCES, f, indent=4)
        print(f"\nDone backing upto {FILENAME}")

    for resource_id, resource in RESOURCES.items():
        _resource = json.loads(resource)  # str -> dict conversion
        _resource["group_masks"] = {args.group_id: {"metadata": "edit",
                                                    "data": "edit",
                                                    "admin": "not-admin"}}
        REDIS_CONN.hset("resources",
                        resource_id,
                        json.dumps(_resource))
    exit("Done updating `resources`\n")
