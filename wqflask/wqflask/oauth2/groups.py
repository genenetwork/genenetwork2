import datetime
from functools import partial

from flask import (
    flash, session, request, url_for, redirect, Response, Blueprint,
    render_template)

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import (
    user_details, handle_error, request_error, process_error, handle_success,
    raise_unimplemented)

groups = Blueprint("group", __name__)

@groups.route("/", methods=["GET"])
def user_group():
    """Get the user's group."""
    def __get_join_requests__(group, users):
        return oauth2_get("oauth2/group/requests/join/list").either(
            lambda error: render_template(
                "oauth2/group.html", group=group, users=users,
                group_join_requests_error=process_error(error)),
            lambda gjr: render_template(
                "oauth2/group.html", group=group, users=users,
                group_join_requests=gjr))
    def __success__(group):
        return oauth2_get(f"oauth2/group/members/{group['group_id']}").either(
            lambda error: render_template(
                "oauth2/group.html", group=group,
                user_error=process_error(error)),
            partial(__get_join_requests__, group))

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

@groups.route("/list-join-requests", methods=["GET"])
@require_oauth2
def list_join_requests() -> Response:
    def __ts_to_dt_str__(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).isoformat()
    def __fail__(error):
        return render_template(
            "oauth2/join-requests.html", error=process_error(error),
            requests=[])
    def __success__(requests):
        return render_template(
            "oauth2/join-requests.html", error=False, requests=requests,
            datetime_string=__ts_to_dt_str__)
    return oauth2_get("oauth2/group/requests/join/list").either(
        __fail__, __success__)

@groups.route("/accept-join-requests", methods=["POST"])
@require_oauth2
def accept_join_request():
    def __fail__(error):
        err=process_error()
        flash("{}", "alert-danger")
        return redirect(url_for("oauth2.group.list_join_requests"))
    def __success__(requests):
        flash("Request was accepted successfully.", "alert-success")
        return redirect(url_for("oauth2.group.list_join_requests"))
    return oauth2_post(
        "oauth2/group/requests/join/accept",
        data=request.form).either(
            handle_error("oauth2.group.list_join_requests"),
            __success__)
