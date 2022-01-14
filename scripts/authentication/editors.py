#!/usr/bin/env python3
"""Manually add editors users"""
import redis
import json
import uuid
import datetime

if __name__ == "__main__":
    conn = redis.Redis(decode_responses=True)
    group_uid = ""
    for guid in conn.hgetall("groups"):
        group_details = json.loads(conn.hget("groups", guid))
        if group_details.get("name") == "editors":
            group_uid = guid
            break

    if not group_uid:
        group_uid = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
        conn.hset(
            "groups",
            group_uid,
            json.dumps(
                {
                    "name": "editors",
                    "admins": [],
                    "members": ["8ad942fe-490d-453e-bd37-56f252e41603"],
                    "created_timestamp": timestamp,
                    "changed_timestamp": timestamp,
                }))

    for resource in conn.hgetall("resources"):
        _resource = json.loads(conn.hget("resources", resource))
        _resource["default_mask"] = {
            'data': 'view',
            'metadata': 'view',
            'admin': 'not-admin',
        }
        _resource["group_masks"] = {
            group_uid: {
                'metadata': 'edit',
                'data': 'edit',
                'admin': 'edit-admins',
            }}
        conn.hset("resources", resource, json.dumps(_resource))
    print("Done adding editor's group to resources!")
