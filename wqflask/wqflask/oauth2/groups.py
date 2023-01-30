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
def group_join_or_create():
    user_details = __user_details__()
    if bool(user_details["group"]):
        flash("You are already a member of a group.", "alert info.")
        return redirect(url_for("oauth2.user_profile"))
    groups = oauth2_get("oauth2/groups").either(
        lambda x: __raise_unimplemented__(), lambda x: x)
    return render_template("oauth2/group_join_or_create.html", groups=groups)
