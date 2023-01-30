from flask import Blueprint, render_template

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import __user_details__, __request_error__

groups = Blueprint("group", __name__)

@groups.route("/", methods=["GET"])
def user_group():
    def __success__(group):
        return render_template("oauth2/group.html", group=group)

    return oauth2_get("oauth2/user-group").either(
        __request_error__, __success__)

@groups.route("/create", methods=["POST"])
@require_oauth2
def create_group():
    def __setup_group__(response):
        session["user_details"]["group"] = response

    resp = oauth2_post("oauth2/create-group", data=dict(request.form))
    return resp.either(
        __handle_error__("oauth2.group_join_or_create"),
        __handle_success__(
            "Created group", "oauth2.user_profile",
            response_handlers=__setup_group__))

@groups.route("/join-or-create", methods=["GET"])
@require_oauth2
def join_or_create():
    user_details = __user_details__()
    if bool(user_details["group"]):
        flash("You are already a member of a group.", "alert info.")
        return redirect(url_for("oauth2.user_profile"))
    groups = oauth2_get("oauth2/groups").either(
        lambda x: __raise_unimplemented__(), lambda x: x)
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

@groups.route("/<uuid:group_id>/users/list", methods=["GET", "POST"])
@require_oauth2
def list_group_users(group_id):
    return "WOULD LIST GROUP USERS."
