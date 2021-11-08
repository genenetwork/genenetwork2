import redis

from flask import current_app
from flask import Blueprint
from flask import g
from flask import render_template
from gn3.authentication import get_groups_by_user_uid
from wqflask.decorators import login_required

group_management = Blueprint("group_management", __name__)


@group_management.route("/groups")
@login_required
def view_groups():
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
