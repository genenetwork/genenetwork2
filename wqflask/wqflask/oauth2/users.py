from flask import Blueprint, render_template

from .checks import require_oauth2
from .client import oauth2_get, oauth2_client
from .request_utils import __user_details__, __request_error__

users = Blueprint("user", __name__)

@users.route("/profile", methods=["GET"])
@require_oauth2
def user_profile():
    __id__ = lambda the_val: the_val
    user_details = __user_details__()
    client = oauth2_client()

    roles = oauth2_get("oauth2/user-roles").either(lambda x: "Error", lambda x: x)
    return render_template(
        "oauth2/view-user.html", user_details=user_details, roles=roles)

@users.route("/request-add-to-group", methods=["POST"])
@require_oauth2
def request_add_to_group():
    return "WOULD SEND MESSAGE TO HAVE YOU ADDED TO GROUP..."

@users.route("/group", methods=["GET"])
def user_group():
    def __success__(group):
        return render_template("oauth2/group.html", group=group)

    return oauth2_get("oauth2/user-group").either(
        __request_error__, __success__)
