from uuid import UUID

from flask import (
    flash, request, url_for, redirect, Response, Blueprint)

from . import client
from .ui import render_ui as _render_ui
from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import (flash_error,
                            flash_success,
                            request_error,
                            process_error,
                            with_flash_error,
                            with_flash_success)

resources = Blueprint("resource", __name__)

def render_ui(template, **kwargs):
    return _render_ui(template, uipages="resources", **kwargs)

@resources.route("/", methods=["GET"])
@require_oauth2
def user_resources():
    """List the resources the user has access to."""
    def __success__(resources):
        return render_ui("oauth2/resources.html", resources=resources)

    return oauth2_get("auth/user/resources").either(
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
        return oauth2_get("auth/resource/categories").either(
            lambda error: __render_template__(error=process_error(
                error, "Could not retrieve resource categories")),
            lambda cats: __render_template__(categories=cats))

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
        "auth/resource/create", json=dict(request.form)).either(
            __perr__, __psuc__)

def __compute_page__(submit, current_page):
    if submit == "next":
        return current_page + 1
    return (current_page - 1) or 1

@resources.route("/<uuid:resource_id>/view", methods=["GET"])
@require_oauth2
def view_resource(resource_id: UUID):
    """View the given resource."""
    page = __compute_page__(request.args.get("submit"),
                            int(request.args.get("page", "1"), base=10))
    count_per_page = int(request.args.get("count_per_page", "100"), base=10)
    def __users_success__(
            resource, unlinked_data, users_n_roles, this_user, resource_roles,
            users):
        return render_ui(
            "oauth2/view-resource.html", resource=resource,
            unlinked_data=unlinked_data, users_n_roles=users_n_roles,
            this_user=this_user, resource_roles=resource_roles, users=users,
            page=page, count_per_page=count_per_page)

    def __resource_roles_success__(
            resource, unlinked_data, users_n_roles, this_user, resource_roles):
        return oauth2_get("auth/user/list").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_data=unlinked_data, users_n_roles=users_n_roles,
                this_user=this_user, resource_roles=resource_roles,
                users_error=process_error(err), count_per_page=count_per_page),
            lambda users: __users_success__(
                resource, unlinked_data, users_n_roles, this_user, resource_roles,
                users))

    def __this_user_success__(resource, unlinked_data, users_n_roles, this_user):
        return oauth2_get(f"auth/resource/{resource_id}/roles").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_data=unlinked_data, users_n_roles=users_n_roles,
                this_user=this_user, resource_roles_error=process_error(err),
                count_per_page=count_per_page),
            lambda rroles: __resource_roles_success__(
                resource, unlinked_data, users_n_roles, this_user, rroles))

    def __users_n_roles_success__(resource, unlinked_data, users_n_roles):
        return oauth2_get("auth/user/").either(
            lambda err: render_ui(
                "oauth2/view-resource.html",
                this_user_error=process_error(err)),
            lambda usr_dets: __this_user_success__(
                resource, unlinked_data, users_n_roles, usr_dets))

    def __unlinked_success__(resource, unlinked_data):
        return oauth2_get(f"auth/resource/{resource_id}/user/list").either(
            lambda err: render_ui(
                "oauth2/view-resource.html",
                resource=resource,
                unlinked_data=unlinked_data,
                users_n_roles_error=process_error(err),
                page=page,
                count_per_page=count_per_page),
            lambda users_n_roles: __users_n_roles_success__(
                resource, unlinked_data, users_n_roles))

    def __resource_success__(resource):
        dataset_type = resource["resource_category"]["resource_category_key"]
        return oauth2_get(f"auth/group/{dataset_type}/unlinked-data").either(
            lambda err: render_ui(
                "oauth2/view-resource.html", resource=resource,
                unlinked_error=process_error(err)),
            lambda unlinked: __unlinked_success__(resource, unlinked))

    def __fetch_resource_data__(resource):
        """Fetch the resource's data."""
        return client.get(
            f"auth/resource/view/{resource['resource_id']}/data?page={page}"
            f"&count_per_page={count_per_page}").either(
                lambda err: {
                    **resource, "resource_data_error": process_error(err)
                },
                lambda resdata: {**resource, "resource_data": resdata})

    return oauth2_get(f"auth/resource/view/{resource_id}").map(
        __fetch_resource_data__).either(
            lambda err: render_ui(
                "oauth2/view-resource.html",
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
        return oauth2_post("auth/resource/data/link", data=dict(form)).either(
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
            "auth/resource/data/unlink", data=dict(form)).either(
            __error__, __success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=form["resource_id"]))

@resources.route("<uuid:resource_id>/user/assign", methods=["POST"])
@require_oauth2
def assign_role(resource_id: UUID) -> Response:
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
            f"auth/resource/{resource_id}/user/assign",
            json={
                "group_role_id": group_role_id,
                "user_email": user_email
            }).either(__assign_error__, __assign_success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for("oauth2.resource.view_resource", resource_id=resource_id))

@resources.route("<uuid:resource_id>/user/unassign", methods=["POST"])
@require_oauth2
def unassign_role(resource_id: UUID) -> Response:
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
            f"auth/resource/{resource_id}/user/unassign",
            json={
                "group_role_id": group_role_id,
                "user_id": user_id
            }).either(__unassign_error__, __unassign_success__)
    except AssertionError as aserr:
        flash(aserr.args[0], "alert-danger")
        return redirect(url_for("oauth2.resource.view_resource", resource_id=resource_id))

@resources.route("/toggle/<uuid:resource_id>", methods=["POST"])
@require_oauth2
def toggle_public(resource_id: UUID):
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
        f"auth/resource/{resource_id}/toggle-public").either(
            lambda err: __handle_error__(err),
            lambda suc: __handle_success__(suc))

@resources.route("/edit/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def edit_resource(resource_id: UUID):
    """Edit the given resource."""
    return "WOULD Edit THE GIVEN RESOURCE'S DETAILS"

@resources.route("/delete/<uuid:resource_id>", methods=["GET"])
@require_oauth2
def delete_resource(resource_id: UUID):
    """Delete the given resource."""
    return "WOULD DELETE THE GIVEN RESOURCE"

@resources.route("/<uuid:resource_id>/roles/<uuid:role_id>", methods=["GET"])
@require_oauth2
def view_resource_role(resource_id: UUID, role_id: UUID):
    """View resource role page."""
    def __render_template__(**kwargs):
        return render_ui("oauth2/view-resource-role.html", **kwargs)

    def __fetch_users__(resource, role, unassigned_privileges):
        return oauth2_get(
            f"auth/resource/{resource_id}/role/{role_id}/users").either(
            lambda error: __render_template__(
                resource=resource,
                role=role,
                unassigned_privileges=unassigned_privileges,
                user_error=process_error(error)),
            lambda users: __render_template__(
                resource=resource,
                role=role,
                unassigned_privileges=unassigned_privileges,
                users=users))

    def __fetch_all_roles__(resource, role):
        return oauth2_get(f"auth/resource/{resource_id}/roles").either(
            lambda error: __render_template__(
                all_roles_error=process_error(error)),
            lambda all_roles: __fetch_users__(
                resource=resource,
                role=role,
                unassigned_privileges=[
                    priv for role in all_roles
                    for priv in role["privileges"]
                    if priv not in role["privileges"]
                ]))

    def __fetch_resource_role__(resource):
        return oauth2_get(
        f"auth/resource/{resource_id}/role/{role_id}").either(
            lambda error: __render_template__(
                resource=resource,
                role_id=role_id,
                role_error=process_error(error)),
            lambda role: __fetch_all_roles__(resource, role))

    return oauth2_get(
        f"auth/resource/view/{resource_id}").either(
            lambda error: __render_template__(
                resource_error=process_error(error)),
            lambda resource: __fetch_resource_role__(resource=resource))

@resources.route("/<uuid:resource_id>/roles/<uuid:role_id>/unassign-privilege",
                 methods=["GET", "POST"])
@require_oauth2
def unassign_privilege_from_resource_role(resource_id: UUID, role_id: UUID):
    """Remove a privilege from a resource role."""
    form = request.form
    returnto = redirect(url_for("oauth2.resource.view_resource_role",
                                resource_id=resource_id,
                                role_id=role_id))
    privilege_id = (request.args.get("privilege_id")
                    or form.get("privilege_id"))
    if not privilege_id:
        flash("You need to specify a privilege to unassign.", "alert-danger")
        return returnto

    if request.method=="POST" and form.get("confirm") == "Unassign":
        return oauth2_post(
            f"auth/resource/{resource_id}/role/{role_id}/unassign-privilege",
            json={
                "privilege_id": form["privilege_id"]
            }).either(with_flash_error(returnto), with_flash_success(returnto))

    if form.get("confirm") == "Cancel":
        flash("Cancelled the operation to unassign the privilege.",
              "alert-info")
        return returnto

    def __fetch_privilege__(resource, role):
        return oauth2_get(
            f"auth/privileges/{privilege_id}/view").either(
                with_flash_error(returnto),
                lambda privilege: render_ui(
                    "oauth2/confirm-resource-role-unassign-privilege.html",
                    resource=resource,
                    role=role,
                    privilege=privilege))

    def __fetch_resource_role__(resource):
        return oauth2_get(
            f"auth/resource/{resource_id}/role/{role_id}").either(
                with_flash_error(returnto),
                lambda role: __fetch_privilege__(resource, role))

    return oauth2_get(
        f"auth/resource/view/{resource_id}").either(
            with_flash_error(returnto),
            __fetch_resource_role__)


@resources.route("/<uuid:resource_id>/roles/create-role",
                 methods=["GET", "POST"])
@require_oauth2
def create_resource_role(resource_id: UUID):
    """Create new role for the resource."""
    def __render__(**kwargs):
        return render_ui("oauth2/create-role.html", **kwargs)

    def __fetch_resource_roles__(resource):
        return oauth2_get(f"auth/resource/{resource_id}/roles").either(
            lambda error: __render__(resource_role_error=error),
            lambda roles: {"resource": resource, "roles": roles})

    if request.method == "GET":
        return oauth2_get(f"auth/resource/view/{resource_id}").map(
            __fetch_resource_roles__).either(
            lambda error: __render__(resource_error=error),
            lambda kwargs: __render__(**kwargs))

    formdata = request.form
    privileges = formdata.getlist("privileges[]")
    if not bool(privileges):
        flash(
            "You must provide at least one privilege for creation of the new "
            "role.",
            "alert-danger")
        return redirect(url_for("oauth2.resource.create_resource_role",
                                resource_id=resource_id))

    def __handle_error__(error):
        flash_error(process_error(error))
        return redirect(url_for(
            "oauth2.resource.create_resource_role", resource_id=resource_id))

    def __handle_success__(success):
        flash("Role successfully created.", "alert-success")
        return redirect(url_for(
            "oauth2.resource.view_resource", resource_id=resource_id))

    return oauth2_post(
        f"auth/resource/{resource_id}/roles/create",
        json={
            "role_name": formdata["role_name"],
            "privileges": privileges
        }).either(
            __handle_error__, __handle_success__)
