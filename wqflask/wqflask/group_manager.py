import json
import redis

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
    return redirect(url_for('group_management.view_groups'))
