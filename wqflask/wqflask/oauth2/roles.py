"""Handle role endpoints"""
import uuid

from flask import Blueprint, render_template

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import request_error

roles = Blueprint("role", __name__)

@roles.route("/user", methods=["GET"])
@require_oauth2
def user_roles():
    def __success__(roles):
        return render_template("oauth2/list_roles.html", roles=roles)

    return oauth2_get("oauth2/user-roles").either(
        request_error, __success__)

@roles.route("/role/<uuid:role_id>", methods=["GET"])
@require_oauth2
def role(role_id: uuid.UUID):
    def __success__(the_role):
        return render_template("oauth2/role.html", role=the_role)

    return oauth2_get(f"oauth2/role/{role_id}").either(
        request_error, __success__)
