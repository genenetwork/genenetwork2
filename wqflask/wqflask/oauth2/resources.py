import uuid

from flask import Blueprint, render_template

from .client import oauth2_get
from .checks import require_oauth2
from .request_utils import request_error

resources = Blueprint("resource", __name__)

@resources.route("/", methods=["GET"])
@require_oauth2
def user_resources():
    """List the resources the user has access to."""
    def __success__(resources):
        return render_template("oauth2/resources.html", resources=resources)

    return oauth2_get("oauth2/user-resources").either(
        request_error, __success__)

@resources.route("/create", methods=["GET"])
@require_oauth2
def create_resource():
    """Create a new resource."""
    return "WOULD CREATE A NEW RESOURCE."

@resources.route("/view/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def view_resource(resource_id: uuid.UUID):
    """View the given resource."""
    # Display the resource's details
    # Provide edit/delete options
    # Metadata edit maybe?
    return "WOULD DISPLAY THE GIVEN RESOURCE'S DETAILS"

@resources.route("/edit/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def edit_resource(resource_id: uuid.UUID):
    """Edit the given resource."""
    return "WOULD Edit THE GIVEN RESOURCE'S DETAILS"

@resources.route("/delete/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def delete_resource(resource_id: uuid.UUID):
    """Delete the given resource."""
    return "WOULD DELETE THE GIVEN RESOURCE"
