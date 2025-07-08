import uuid
import datetime
from functools import partial

from flask import (
    flash, jsonify, request, url_for, redirect, Response, Blueprint)

from .ui import render_ui
from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import (
    user_details, handle_error, process_error, handle_success)

from . import session

groups = Blueprint("group", __name__)

@groups.route("/", methods=["GET"])
def user_group():
    """Get the user's group."""
    def __get_join_requests__(group, users):
        return oauth2_get("auth/group/requests/join/list").either(
            lambda error: render_ui(
                "oauth2/group.html", group=group, users=users,
                group_join_requests_error=process_error(error)),
            lambda gjr: render_ui(
                "oauth2/group.html", group=group, users=users,
                group_join_requests=gjr))
    def __success__(group):
        return oauth2_get(f"auth/group/members/{group['group_id']}").either(
            lambda error: render_ui(
                "oauth2/group.html", group=group,
                user_error=process_error(error)),
            partial(__get_join_requests__, group))

    def __group_error__(err):
        return render_ui(
            "oauth2/group.html", group_error=process_error(err))

    return oauth2_get("auth/user/group").either(
        __group_error__, __success__)

@groups.route("/list", methods=["GET"])
@require_oauth2
def list_groups():
    """List user groups on the system."""
    return render_ui("oauth2/list-groups.html")

@groups.route("/create", methods=["POST"])
@require_oauth2
def create_group():
    def __setup_group__(response):
        user_dets = session.session_info()["user"]
        group_dets = user_details(fetch_remote=True)
        session.set_user_details({**user_dets, "group": group_dets["group"]})

    resp = oauth2_post("auth/group/create", json=dict(request.form))
    return resp.either(
        handle_error("oauth2.group.join_or_create"),
        handle_success(
            "Created group", "oauth2.user.user_profile",
            response_handlers=[__setup_group__]))

@groups.route("/join-or-create", methods=["GET"])
@require_oauth2
def join_or_create():
    usr_dets = user_details()
    if bool(usr_dets.get("group")):
        flash("You are already a member of a group.", "alert-info")
        return redirect(url_for("oauth2.user.user_profile"))
    def __group_error__(err):
        return render_ui(
            "oauth2/group_join_or_create.html", groups=[],
            groups_error=process_error(err))
    def __group_success__(groups):
        return oauth2_get("auth/user/group/join-request").either(
            __gjr_error__, partial(__gjr_success__, groups=groups))
    def __gjr_error__(err):
        return render_ui(
            "oauth2/group_join_or_create.html", groups=[],
            gjr_error=process_error(err))
    def __gjr_success__(gjr, groups):
        return render_ui(
            "oauth2/group_join_or_create.html", groups=groups,
            group_join_request=gjr)
    return oauth2_get("auth/group/list").either(
        __group_error__, __group_success__)

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
        return render_ui(
            "oauth2/join-requests.html", error=process_error(error),
            requests=[])
    def __success__(requests):
        return render_ui(
            "oauth2/join-requests.html", error=False, requests=requests,
            datetime_string=__ts_to_dt_str__)
    return oauth2_get("auth/group/requests/join/list").either(
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
        "auth/group/requests/join/accept",
        json=dict(request.form)).either(
            handle_error("oauth2.group.list_join_requests"),
            __success__)

@groups.route("/reject-join-requests", methods=["POST"])
@require_oauth2
def reject_join_request():
    def __fail__(error):
        err=process_error()
        flash(f"{err['error']}: {err['error_description']}", "alert-danger")
        return redirect(url_for("oauth2.group.list_join_requests"))
    def __success__(requests):
        flash("Request was rejected successfully.", "alert-success")
        return redirect(url_for("oauth2.group.list_join_requests"))
    return oauth2_post(
        "auth/group/requests/join/reject",
        json=dict(request.form)).either(
            handle_error("oauth2.group.list_join_requests"),
            __success__)


def add_delete_privilege_to_role(
        group_role_id: uuid.UUID, direction: str) -> Response:
    """Add/delete a privilege to/from a role depending on `direction`."""
    assert direction in ("ADD", "DELETE")
    def __render__():
        return redirect(url_for(
            "oauth2.group.group_role", group_role_id=group_role_id))

    def __error__(error):
        err = process_error(error)
        flash(f"{err['error']}: {err['error_description']}", "alert-danger")
        return __render__()

    def __success__(success):
        flash(success["description"], "alert-success")
        return __render__()
    try:
        form = request.form
        privilege_id = form.get("privilege_id")
        assert bool(privilege_id), "Privilege to add must be provided"
        uris = {
            "ADD": f"auth/group/role/{group_role_id}/privilege/add",
            "DELETE": f"auth/group/role/{group_role_id}/privilege/delete"
        }
        return oauth2_post(
            uris[direction],
            json={
                "group_role_id": group_role_id,
                "privilege_id": privilege_id
            }).either(__error__, __success__)
    except AssertionError as aerr:
        flash(aerr.args[0], "alert-danger")
        return redirect(url_for(
            "oauth2.group.group_role", group_role_id=group_role_id))

@groups.route("/role/<uuid:group_role_id>/privilege/add", methods=["POST"])
@require_oauth2
def add_privilege_to_role(group_role_id: uuid.UUID):
    """Add a privilege to a group role."""
    return add_delete_privilege_to_role(group_role_id, "ADD")

@groups.route("/role/<uuid:group_role_id>/privilege/delete", methods=["POST"])
@require_oauth2
def delete_privilege_from_role(group_role_id: uuid.UUID):
    """Delete a privilege from a group role."""
    return add_delete_privilege_to_role(group_role_id, "DELETE")


@groups.route("/fetch", methods=["GET", "POST"])
@require_oauth2
def fetch_groups():
    draw = request.args["draw"]
    search = request.args.get("search[value]")
    return jsonify(oauth2_get(
        "auth/group/list",
        json={
            "search": search,
            "start": request.args.get("start") or "0",
            "length": request.args.get("length") or "0"
        }
    ).either(
        lambda err: {
            "draw": draw,
            **process_error(err)
        },
        lambda results: {
            "draw": draw,
            "groups": results["groups"],
            "recordsTotal": results["total-groups"],
            "recordsFiltered": results["total-filtered"]
        }))


@groups.route("/view/<uuid:group_id>", methods=["GET"])
def view_group(group_id: uuid.UUID):
    """View a specific group's details."""
    def __fetch_users__(group):
        return oauth2_get(f"auth/group/members/{group_id}").then(
            lambda users: {"group": group, "members": users})

    def __fetch_resources__(group_details):
        return oauth2_get(f"auth/group/data-resources/{group_id}").then(
            lambda resources: {**group_details, "resources": resources})

    return oauth2_get(f"auth/group/{group_id}").then(
        __fetch_users__
    ).then(
        __fetch_resources__
    ).then(
        lambda _dets: render_ui("oauth2/group.html", **_dets)
    ).either(
        lambda err: render_ui("oauth2/request_error.html",
                              response=err),
        lambda response: response)
