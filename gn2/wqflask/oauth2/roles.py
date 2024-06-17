"""Handle role endpoints"""
import uuid

from flask import flash, request, url_for, redirect, Blueprint

from .ui import render_ui
from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import request_error, process_error

roles = Blueprint("role", __name__)

@roles.route("/role/<uuid:role_id>", methods=["GET"])
@require_oauth2
def role(role_id: uuid.UUID):
    def __success__(the_role):
        return render_ui("oauth2/role.html",
                         role=the_role[0],
                         resource_id=uuid.UUID(the_role[1]))

    return oauth2_get(f"auth/role/view/{role_id}").either(
        request_error, __success__)

