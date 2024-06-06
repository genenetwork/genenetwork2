"""Handle role endpoints"""
import uuid

from flask import flash, request, url_for, redirect, Blueprint

from .ui import render_ui
from .checks import require_oauth2
from .client import oauth2_get, oauth2_post
from .request_utils import request_error, process_error

roles = Blueprint("role", __name__)

@roles.route("/user", methods=["GET"])
@require_oauth2
def user_roles():
    def  __grerror__(roles, user_privileges, error):
        return render_ui(
            "oauth2/list_roles.html", roles=roles,
            user_privileges=user_privileges,
            group_roles_error=process_error(error))

    def  __grsuccess__(roles, user_privileges, group_roles):
        return render_ui(
            "oauth2/list_roles.html", roles=roles,
            user_privileges=user_privileges, group_roles=group_roles)

    def __role_success__(roles):
        uprivs = tuple(
            privilege["privilege_id"] for role in roles
            for privilege in role["privileges"])
        return oauth2_get("auth/group/roles").either(
            lambda err: __grerror__(roles, uprivs, err),
            lambda groles: __grsuccess__(roles, uprivs, groles))

    return oauth2_get("auth/system/roles").either(
        request_error, __role_success__)

@roles.route("/role/<uuid:role_id>", methods=["GET"])
@require_oauth2
def role(role_id: uuid.UUID):
    def __success__(the_role):
        return render_ui("oauth2/role.html",
                         role=the_role[0],
                         resource_id=uuid.UUID(the_role[1]))

    return oauth2_get(f"auth/role/view/{role_id}").either(
        request_error, __success__)

@roles.route("/create", methods=["GET", "POST"])
@require_oauth2
def create_role():
    """Create a new role."""
    def __roles_error__(error):
        return render_ui(
            "oauth2/create-role.html", roles_error=process_error(error))

    def __gprivs_error__(roles, error):
        return render_ui(
            "oauth2/create-role.html", roles=roles,
            group_privileges_error=process_error(error))

    def __success__(roles, gprivs):
        uprivs = tuple(
            privilege["privilege_id"] for role in roles
            for privilege in role["privileges"])
        return render_ui(
            "oauth2/create-role.html", roles=roles, user_privileges=uprivs,
            group_privileges=gprivs,
            prev_role_name=request.args.get("role_name"))

    def __fetch_gprivs__(roles):
        return oauth2_get("auth/group/privileges").either(
            lambda err: __gprivs_error__(roles, err),
            lambda gprivs: __success__(roles, gprivs))

    if request.method == "GET":
        return oauth2_get("auth/user/roles").either(
            __roles_error__, __fetch_gprivs__)

    form = request.form
    role_name = form.get("role_name")
    privileges = form.getlist("privileges[]")
    if len(privileges) == 0:
        flash("You must assign at least one privilege to the role",
              "alert-danger")
        return redirect(url_for(
            "oauth2.role.create_role", role_name=role_name))
    def __create_error__(error):
        err = process_error(error)
        flash(f"{err['error']}: {err['error_description']}",
              "alert-danger")
        return redirect(url_for("oauth2.role.create_role"))
    def __create_success__(*args):
        flash("Role created successfully.", "alert-success")
        return redirect(url_for("oauth2.role.user_roles"))

    raise DeprecationWarning(
        f"The `{__name__}.create_role(…)` function, as is currently, can "
        "lead to unbounded privilege escalation. See "
        "https://issues.genenetwork.org/issues/gn-auth/problems-with-roles")
    # return oauth2_post(
    #     "auth/group/role/create",data={
    #         "role_name": role_name, "privileges[]": privileges}).either(
    #     __create_error__,__create_success__)
