from flask import (
    flash, session, request, url_for, redirect, Blueprint, render_template)

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import (
    user_details, handle_error, request_error, process_error, handle_success,
    raise_unimplemented)

groups = Blueprint("group", __name__)

@groups.route("/", methods=["GET"])
def user_group():
    """Get the user's group."""

    def __success__(group):
        return oauth2_get(f"oauth2/group/members/{group['group_id']}").either(
            lambda error: render_template(
                "oauth2/group.html", group=group,
                user_error=process_error(error)),
            lambda users: render_template(
                "oauth2/group.html", group=group, users=users))

    return oauth2_get("oauth2/user/group").either(
        request_error, __success__)

@groups.route("/create", methods=["POST"])
@require_oauth2
def create_group():
    def __setup_group__(response):
        session["user_details"]["group"] = response

    resp = oauth2_post("oauth2/group/create", data=dict(request.form))
    return resp.either(
        handle_error("oauth2.group.join_or_create"),
        handle_success(
            "Created group", "oauth2.user.user_profile",
            response_handlers=[__setup_group__]))

@groups.route("/join-or-create", methods=["GET"])
@require_oauth2
def join_or_create():
    usr_dets = user_details()
    if bool(usr_dets["group"]):
        flash("You are already a member of a group.", "alert-info")
        return redirect(url_for("oauth2.user.user_profile"))
    groups = oauth2_get("oauth2/group/list").either(
        lambda x: raise_unimplemented(), lambda x: x)
    return render_template("oauth2/group_join_or_create.html", groups=groups)

@groups.route("/delete/<uuid:group_id>", methods=["GET", "POST"])
@require_oauth2
def delete_group(group_id):
    """Delete the user's group."""
    return "WOULD DELETE GROUP."

@groups.route("/edit/<uuid:group_id>", methods=["GET", "POST"])
@require_oauth2
def edit_group(group_id):
    """Edit the user's group."""
    return "WOULD EDIT GROUP."
