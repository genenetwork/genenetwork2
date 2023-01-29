from flask import Blueprint, render_template

from .client import oauth2_get
from .checks import require_oauth2
from .request_utils import __request_error__

resources = Blueprint("resource", __name__)

@resources.route("/", methods=["GET"])
@require_oauth2
def user_resources():
    def __success__(resources):
        return render_template("oauth2/resources.html", resources=resources)

    return oauth2_get("oauth2/user-resources").either(
        __request_error__, __success__)
