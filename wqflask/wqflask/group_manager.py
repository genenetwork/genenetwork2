import json
import redis
import datetime

from flask import current_app
from flask import Blueprint
from flask import g
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from gn3.authentication import get_groups_by_user_uid
from gn3.authentication import get_user_info_by_key
from gn3.authentication import create_group
from wqflask.decorators import login_required

group_management = Blueprint("group_management", __name__)


@group_management.route("/groups")
@login_required
def display_groups():
    groups = get_groups_by_user_uid(
        user_uid=(g.user_session.record.get(b"user_id",
                                            b"").decode("utf-8") or
                  g.user_session.record.get("user_id", "")),
        conn=redis.from_url(
            current_app.config["REDIS_URL"],
            decode_responses=True))
    return render_template("admin/group_manager.html",
                           admin_groups=groups.get("admin"),
                           member_groups=groups.get("member"))


@group_management.route("/groups/create", methods=("GET",))
@login_required
def view_create_group_page():
    return render_template("admin/create_group.html")


@group_management.route("/groups/create", methods=("POST",))
@login_required
def create_new_group():
    conn = redis.from_url(current_app.config["REDIS_URL"],
                          decode_responses=True)
    if group_name := request.form.get("group_name"):
        members_uid, admins_uid = set(), set()
        admins_uid.add(user_uid := (
            g.user_session.record.get(
                b"user_id",
                b"").decode("utf-8") or
            g.user_session.record.get("user_id", "")))
        if admin_string := request.form.get("admin_emails_to_add"):
            for email in admin_string.split(","):
                user_info = get_user_info_by_key(key="email_address",
                                                 value=email,
                                                 conn=conn)
                if user_uid := user_info.get("user_id"):
                    admins_uid.add(user_uid)
        if member_string := request.form.get("member_emails_to_add"):
            for email in member_string.split(","):
                user_info = get_user_info_by_key(key="email_address",
                                                 value=email,
                                                 conn=conn)
                if user_uid := user_info.get("user_id"):
                    members_uid.add(user_uid)

        # Create the new group:
        create_group(conn=conn,
                     group_name=group_name,
                     member_user_uids=list(members_uid),
                     admin_user_uids=list(admins_uid))
        return redirect(url_for('group_management.display_groups'))
    return redirect(url_for('group_management.create_groups'))


@group_management.route("/groups/delete", methods=("POST",))
@login_required
def delete_groups():
    conn = redis.from_url(current_app.config["REDIS_URL"],
                          decode_responses=True)
    user_uid = (g.user_session.record.get(b"user_id", b"").decode("utf-8") or
                g.user_session.record.get("user_id", ""))
    current_app.logger.info(request.form.get("selected_group_ids"))
    for group_uid in request.form.get("selected_group_ids", "").split(":"):
        if group_info := conn.hget("groups", group_uid):
            group_info = json.loads(group_info)
            # A user who is an admin can delete things
            if user_uid in group_info.get("admins"):
                conn.hdel("groups", group_uid)
    return redirect(url_for('group_management.display_groups'))


@group_management.route("/groups/<group_id>")
@login_required
def view_group(group_id: str):
    conn = redis.from_url(current_app.config["REDIS_URL"],
                          decode_responses=True)
    user_uid = (g.user_session.record.get(b"user_id", b"").decode("utf-8") or
                g.user_session.record.get("user_id", ""))

    resource_info = []
    for resource_uid, resource in conn.hgetall("resources").items():
        resource = json.loads(resource)
        if group_id in (group_mask := resource.get("group_masks")):
            __dict = {}
            for val in group_mask.values():
                __dict.update(val)
            __dict.update({
                "id": resource_uid,
                "name": resource.get("name"),
            })
            resource_info.append(__dict)
    group_info = json.loads(conn.hget("groups",
                                      group_id))
    group_info["guid"] = group_id

    return render_template(
         "admin/view_group.html",
         group_info=group_info,
         admins=[get_user_info_by_key(key="user_id",
                                      value=user_id,
                                      conn=conn)
                 for user_id in group_info.get("admins")],
         members=[get_user_info_by_key(key="user_id",
                                      value=user_id,
                                      conn=conn)
                 for user_id in group_info.get("members")],
         is_admin = (True if user_uid in group_info.get("admins") else False),
         resources=resource_info)
            

@group_management.route("/groups/<group_id>", methods=("POST",))
def update_group(group_id: str):
    conn = redis.from_url(current_app.config["REDIS_URL"],
                          decode_responses=True)
    user_uid = (g.user_session.record.get(b"user_id", b"").decode("utf-8") or
                g.user_session.record.get("user_id", ""))
    group = json.loads(conn.hget("groups", group_id))
    timestamp = group["changed_timestamp"]
    timestamp_ = datetime.datetime.utcnow().strftime('%b %d %Y %I:%M%p')
    if user_uid in group.get("admins"):
        if name := request.form.get("new_name"):
            group["name"] = name
            group["changed_timestamp"] = timestamp_
        if admins := request.form.get("admin_emails_to_add"):
            group["admins"] = list(set(admins.split(":") +
                                       group.get("admins")))
            group["changed_timestamp"] = timestamp_
        if members := request.form.get("member_emails_to_add"):
            print(f"\n+++++\n{members}\n+++++\n")
            group["members"] = list(set(members.split(":") +
                                        group.get("members")))
            group["changed_timestamp"] = timestamp_
        conn.hset("groups", group_id, json.dumps(group))
    return redirect(url_for('group_management.view_group',
                            group_id=group_id))
