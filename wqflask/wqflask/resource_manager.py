import json
import redis
import requests

from flask import Blueprint
from flask import current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from typing import Dict, Tuple
from urllib.parse import urljoin

from wqflask.access_roles import AdminRole
from wqflask.access_roles import DataRole
from wqflask.decorators import edit_access_required
from wqflask.decorators import edit_admins_access_required
from wqflask.decorators import login_required


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


def get_user_access_roles(
        resource_id: str,
        user_id: str,
        gn_proxy_url: str = "http://localhost:8080") -> Dict:
    """Get the highest access roles for a given user

    Args:
      - resource_id: The unique id of a given resource.
      - user_id: The unique id of a given user.
      - gn_proxy_url: The URL where gn-proxy is running.

    Returns:
      A dict indicating the highest access role the user has.

    """
    role_mapping = {}
    for x, y in zip(DataRole, AdminRole):
        role_mapping.update({x.value: x, })
        role_mapping.update({y.value: y, })
    access_role = {}
    for key, value in json.loads(
        requests.get(urljoin(
            gn_proxy_url,
            ("available?resource="
             f"{resource_id}&user={user_id}"))).content).items():
        access_role[key] = max(map(lambda x: role_mapping[x], value))
    return access_role


def add_extra_resource_metadata(conn: redis.Redis,
                                resource_id: str,
                                resource: Dict) -> Dict:
    """If resource['owner_id'] exists, add metadata about that user. Also,
if the resource contains group masks, add the group name into the
resource dict. Note that resource['owner_id'] and the group masks are
unique identifiers so they aren't human readable names.

    Args:
      - conn: A redis connection with the responses decoded.
      - resource_id: The unique identifier of the resource.
      - resource: A dict containing details(metadata) about a
        given resource.

    Returns:
      An embellished dictionary with its resource id; the human
    readable names of the group masks; and the owner id if it was set.

    """
    resource["resource_id"] = resource_id

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
def view_resource(resource_id: str):
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
        resource_info=(add_extra_resource_metadata(
            conn=redis_conn,
            resource_id=resource_id,
            resource=json.loads(resource))),
        access_role=get_user_access_roles(
            resource_id=resource_id,
            user_id=user_id,
            gn_proxy_url=current_app.config.get("GN2_PROXY")))


@resource_management.route("/resources/<resource_id>/make-public",
                           methods=('POST',))
@edit_access_required
@login_required
def update_resource_publicity(resource_id: str):
    redis_conn = redis.from_url(
        current_app.config["REDIS_URL"],
        decode_responses=True)
    resource_info = json.loads(redis_conn.hget("resources", resource_id))

    if (is_open_to_public := request
        .form
        .to_dict()
            .get("open_to_public")) == "True":
        resource_info['default_mask'] = {
            'data': DataRole.VIEW.value,
            'admin': AdminRole.NOT_ADMIN.value,
            'metadata': DataRole.VIEW.value,
        }
    elif is_open_to_public == "False":
        resource_info['default_mask'] = {
            'data': DataRole.NO_ACCESS.value,
            'admin': AdminRole.NOT_ADMIN.value,
            'metadata': DataRole.NO_ACCESS.value,
        }
    redis_conn.hset("resources", resource_id, json.dumps(resource_info))
    return redirect(url_for("resource_management.view_resource",
                            resource_id=resource_id))


@resource_management.route("/resources/<resource_id>/change-owner")
@edit_admins_access_required
@login_required
def view_resource_owner(resource_id: str):
    return render_template(
        "admin/change_resource_owner.html",
        resource_id=resource_id)


@resource_management.route("/resources/<resource_id>/change-owner",
                           methods=('POST',))
@edit_admins_access_required
@login_required
def change_owner(resource_id: str):
    if user_id := request.form.get("new_owner"):
        redis_conn = redis.from_url(
            current_app.config["REDIS_URL"],
            decode_responses=True)
        resource = json.loads(redis_conn.hget("resources", resource_id))
        resource["owner_id"] = user_id
        redis_conn.hset("resources", resource_id, json.dumps(resource))
        flash("The resource's owner has been changed.", "alert-info")
    return redirect(url_for("resource_management.view_resource",
                            resource_id=resource_id))


@resource_management.route("<resource_id>/users/search", methods=('POST',))
@edit_admins_access_required
@login_required
def search_user(resource_id: str):
    results = {}
    for user in (users := redis.from_url(
            current_app.config["REDIS_URL"],
            decode_responses=True).hgetall("users")):
        user = json.loads(users[user])
        for q in (request.form.get("user_name"),
                  request.form.get("user_email")):
            if q and (q in user.get("email_address") or
                      q in user.get("full_name")):
                results[user.get("user_id", "")] = user
    return json.dumps(tuple(results.values()))
