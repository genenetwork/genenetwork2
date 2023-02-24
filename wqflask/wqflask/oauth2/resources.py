import uuid

from flask import flash, request, url_for, redirect, Blueprint, render_template

from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import request_error, process_error

resources = Blueprint("resource", __name__)

@resources.route("/", methods=["GET"])
@require_oauth2
def user_resources():
    """List the resources the user has access to."""
    def __success__(resources):
        return render_template("oauth2/resources.html", resources=resources)

    return oauth2_get("oauth2/user/resources").either(
        request_error, __success__)

@resources.route("/create", methods=["GET", "POST"])
@require_oauth2
def create_resource():
    """Create a new resource."""
    def __render_template__(categories=[], error=None):
        return render_template(
            "oauth2/create-resource.html",
            resource_categories=categories,
            resource_category_error=error)

    if request.method == "GET":
        return oauth2_get("oauth2/resource/categories").either(
            lambda error: __render_template__(error=process_error(
                error, "Could not retrieve resource categories")),
            lambda cats: __render_template__(categories=cats))

    from flask import jsonify
    def __perr__(error):
        err = process_error(error)
        print(f"THE ERROR: {err}")
        flash(f"{err['error']}: {err['error_message']}", "alert-danger")
        return redirect(url_for("oauth2.resource.user_resources"))
    def __psuc__(succ):
        flash("Resource created successfully", "alert-success")
        return redirect(url_for("oauth2.resource.user_resources"))
    return oauth2_post(
        "oauth2/resource/create", data=request.form).either(
            __perr__, __psuc__)

@resources.route("/view/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def view_resource(resource_id: uuid.UUID):
    """View the given resource."""
    # Display the resource's details
    # Provide edit/delete options
    # Metadata edit maybe?
    def __resource_success__(resource):
        dataset_type = resource["resource_category"]["resource_category_key"]
        return oauth2_get(f"oauth2/group/{dataset_type}/unlinked-data").either(
            lambda err: render_template(
                "oauth2/view-resource.html", resource=resource,
                unlinked_error=process_error(err)),
            lambda unlinked: render_template(
                "oauth2/view-resource.html", resource=resource, error=None,
                unlinked_data=unlinked))

    return oauth2_get(f"oauth2/resource/view/{resource_id}").either(
        lambda err: render_template("oauth2/view-resource.html",
                                    resource=None, error=process_error(err)),
        __resource_success__)

@resources.route("/data/link", methods=["POST"])
@require_oauth2
def link_data_to_resource():
    """Link group data to a resource"""
    form = request.form
    try:
        assert "resource_id" in form, "Resource ID not provided."
        assert "dataset_id" in form, "Dataset ID not provided."
        assert "dataset_type" in form, "Dataset type not specified"
        assert form["dataset_type"].lower() in (
            "mrna", "genotype", "phenotype"), "Invalid dataset type provided."
        resource_id = form["resource_id"]

        def __error__(error):
            err = process_error(error)
            flash(f"{err['error']}: {err['error_description']}", "alert-danger")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        def __success__(success):
            flash(f"Data linked to resource successfully", "alert-success")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))
        return oauth2_post("oauth2/resource/data/link", data=dict(form)).either(
            __error__,
            __success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=form["resource_id"]))

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
