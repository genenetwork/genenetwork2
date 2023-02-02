from flask import Blueprint, render_template

from .checks import require_oauth2
from .client import oauth2_get, oauth2_client
from .request_utils import user_details, request_error

users = Blueprint("user", __name__)

@users.route("/profile", methods=["GET"])
@require_oauth2
def user_profile():
    __id__ = lambda the_val: the_val
    usr_dets = user_details()
    client = oauth2_client()

    roles = oauth2_get("oauth2/user/roles").either(lambda x: "Error", lambda x: x)
    return render_template(
        "oauth2/view-user.html", user_details=usr_dets, roles=roles)

@users.route("/request-add-to-group", methods=["POST"])
@require_oauth2
def request_add_to_group():
    return "WOULD SEND MESSAGE TO HAVE YOU ADDED TO GROUP..."
