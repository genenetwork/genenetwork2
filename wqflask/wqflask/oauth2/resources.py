import uuid

from flask import flash, request, url_for, redirect, Response, Blueprint

from .ui import render_ui
from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import (
    flash_error, flash_success, request_error, process_error)

resources = Blueprint("resource", __name__)

@resources.route("/", methods=["GET"])
@require_oauth2
def user_resources():
    """List the resources the user has access to."""
    def __success__(resources):
        return render_ui("oauth2/resources.html", resources=resources)

    return oauth2_get("oauth2/user/resources").either(
        request_error, __success__)

@resources.route("/create", methods=["GET", "POST"])
@require_oauth2
def create_resource():
    """Create a new resource."""
    def __render_template__(categories=[], error=None):
        return render_ui(
            "oauth2/create-resource.html",
            resource_categories=categories,
            resource_category_error=error,
            resource_name=request.args.get("resource_name"),
            resource_category=request.args.get("resource_category"))

    if request.method == "GET":
        return oauth2_get("oauth2/resource/categories").either(
            lambda error: __render_template__(error=process_error(
                error, "Could not retrieve resource categories")),
            lambda cats: __render_template__(categories=cats))

    from flask import jsonify
    def __perr__(error):
        err = process_error(error)
        flash(f"{err['error']}: {err['error_description']}", "alert-danger")
        return redirect(url_for(
            "oauth2.resource.create_resource",
            resource_name=request.form.get("resource_name"),
            resource_category=request.form.get("resource_category")))
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
    def __users_success__(
            resource, unlinked_data, users_n_roles, this_user, group_roles,
            users):
        return render_ui(
            "oauth2/view-resource.html", resource=resource,
            unlinked_data=unlinked_data, users_n_roles=users_n_roles,
            this_user=this_user, group_roles=group_roles, users=users)

    def __group_roles_success__(
            resource, unlinked_data, users_n_roles, this_user, group_roles):
        return oauth2_get("oauth2/user/list").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_data=unlinked_data, users_n_roles=users_n_roles,
                this_user=this_user, group_roles=group_roles,
                users_error=process_error(err)),
            lambda users: __users_success__(
                resource, unlinked_data, users_n_roles, this_user, group_roles,
                users))

    def __this_user_success__(resource, unlinked_data, users_n_roles, this_user):
        return oauth2_get("oauth2/group/roles").either(
            lambda err: render_ui(
                "oauth2/view-resources.html", resource=resource,
                unlinked_data=unlinked_data, users_n_roles=users_n_roles,
                this_user=this_user, group_roles_error=process_error(err)),
            lambda groles: __group_roles_success__(
                resource, unlinked_data, users_n_roles, this_user, groles))

    def __users_n_roles_success__(resource, unlinked_data, users_n_roles):
        return oauth2_get("oauth2/user").either(
            lambda err: render_ui(
                "oauth2/view-resources.html",
                this_user_error=process_error(err)),
            lambda usr_dets: __this_user_success__(
                resource, unlinked_data, users_n_roles, usr_dets))

    def __unlinked_success__(resource, unlinked_data):
        return oauth2_get(f"oauth2/resource/{resource_id}/user/list").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_data=unlinked_data,
                users_n_roles_error=process_error(err)),
            lambda users_n_roles: __users_n_roles_success__(
                resource, unlinked_data, users_n_roles))
        return render_ui(
                "oauth2/view-resource.html", resource=resource, error=None,
                unlinked_data=unlinked)

    def __resource_success__(resource):
        dataset_type = resource["resource_category"]["resource_category_key"]
        return oauth2_get(f"oauth2/group/{dataset_type}/unlinked-data").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_error=process_error(err)),
            lambda unlinked: __unlinked_success__(resource, unlinked))

    return oauth2_get(f"oauth2/resource/view/{resource_id}").either(
        lambda err: render_ui("oauth2/view-resource.html",
                              resource=None, resource_error=process_error(err)),
        __resource_success__)

@resources.route("/data/link", methods=["POST"])
@require_oauth2
def link_data_to_resource():
    """Link group data to a resource"""
    form = request.form
    try:
        assert "resource_id" in form, "Resource ID not provided."
        assert "data_link_id" in form, "Data Link ID not provided."
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

@resources.route("/data/unlink", methods=["POST"])
@require_oauth2
def unlink_data_from_resource():
    """Unlink group data from a resource"""
    form = request.form
    try:
        assert "resource_id" in form, "Resource ID not provided."
        assert "data_link_id" in form, "Data Link ID not provided."
        resource_id = form["resource_id"]

        def __error__(error):
            err = process_error(error)
            flash(f"{err['error']}: {err['error_description']}", "alert-danger")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        def __success__(success):
            flash(f"Data unlinked from resource successfully", "alert-success")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))
        return oauth2_post(
            "oauth2/resource/data/unlink", data=dict(form)).either(
            __error__, __success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=form["resource_id"]))

@resources.route("<uuid:resource_id>/user/assign", methods=["POST"])
@require_oauth2
def assign_role(resource_id: uuid.UUID) -> Response:
    form = request.form
    group_role_id = form.get("group_role_id", "")
    user_email = form.get("user_email", "")
    try:
        assert bool(group_role_id), "The role must be provided."
        assert bool(user_email), "The user email must be provided."

        def __assign_error__(error):
            err = process_error(error)
            flash(f"{err['error']}: {err['error_description']}", "alert-danger")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        def __assign_success__(success):
            flash(success["description"], "alert-success")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        return oauth2_post(
            f"oauth2/resource/{resource_id}/user/assign",
            data={
                "group_role_id": group_role_id,
                "user_email": user_email
            }).either(__assign_error__, __assign_success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for("oauth2.resources.view_resource", resource_id=resource_id))

@resources.route("<uuid:resource_id>/user/unassign", methods=["POST"])
@require_oauth2
def unassign_role(resource_id: uuid.UUID) -> Response:
    form = request.form
    group_role_id = form.get("group_role_id", "")
    user_id = form.get("user_id", "")
    try:
        assert bool(group_role_id), "The role must be provided."
        assert bool(user_id), "The user id must be provided."

        def __unassign_error__(error):
            err = process_error(error)
            flash(f"{err['error']}: {err['error_description']}", "alert-danger")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        def __unassign_success__(success):
            flash(success["description"], "alert-success")
            return redirect(url_for(
                "oauth2.resource.view_resource", resource_id=resource_id))

        return oauth2_post(
            f"oauth2/resource/{resource_id}/user/unassign",
            data={
                "group_role_id": group_role_id,
                "user_id": user_id
            }).either(__unassign_error__, __unassign_success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for("oauth2.resources.view_resource", resource_id=resource_id))

@resources.route("/toggle/<uuid:resource_id>", methods=["POST"])
@require_oauth2
def toggle_public(resource_id: uuid.UUID):
    """Toggle the given resource's public status."""
    def __handle_error__(err):
        flash_error(process_error(err))
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=resource_id))

    def __handle_success__(success):
        flash_success(success)
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=resource_id))

    return oauth2_post(
        f"oauth2/resource/{resource_id}/toggle-public", data={}).either(
            lambda err: __handle_error__(err),
            lambda suc: __handle_success__(suc))

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
