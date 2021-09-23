"""A script that adds the group: 'editors' to every
resource. 'editors' should have the right to edit both metadata and
data.

To use this script, simply run:

.. code-block:: python
   python resource.py

"""
import json
import redis


if __name__ == "__main__":
    REDIS_CONN = redis.Redis()
    resources = REDIS_CONN.hgetall("resources_clone")
    for resource_id, resource in resources.items():
        deserialized_resource = json.loads(resource)
        deserialized_resource["group_masks"] = {
            "editors": {"metadata": "edit",
                        "data": "edit"}}
        REDIS_CONN.hset("resources_clone",
                        resource_id,
                        json.dumps(deserialized_resource))
