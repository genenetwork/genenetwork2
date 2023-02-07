from flask import (
    flash, request, url_for, redirect, Response, Blueprint, render_template)

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post, oauth2_client
from .request_utils import user_details, request_error, process_error

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
def request_add_to_group() -> Response:
    """Request to be added to a group."""
    form = request.form
    group_id = form["group"]

    def __error__(error):
        err = process_error(error)
        flash(f"{err['error']}: {err['error_message']}", "alert-danger")
        return redirect(url_for("oauth2.user.user_profile"))

    def __success__(response):
        flash(f"{response['message']} (Response ID: {response['request_id']})",
              "alert-success")
        return redirect(url_for("oauth2.user.user_profile"))

    return oauth2_post(f"oauth2/group/requests/join/{group_id}",
                       data=form).either(__error__, __success__)
