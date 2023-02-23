"""Handle linking data to groups."""
from flask import (
    flash, request, url_for, redirect, Response, Blueprint, render_template)

from .request_utils import process_error
from .client import oauth2_get, oauth2_post

data = Blueprint("data", __name__)

@data.route("/list", methods=["GET", "POST"])
def list_data():
    """List ungrouped data."""
    def __render__(**kwargs):
        roles = kwargs.get("roles", [])
        user_privileges = tuple(
                privilege["privilege_id"] for role in roles
                for privilege in role["privileges"])
        return render_template(
            "oauth2/data-list.html",
            groups=kwargs.get("groups", []),
            data_items=kwargs.get("data_items", []),
            user_privileges=user_privileges,
            **{key:val for key,val in kwargs.items()
               if key not in ("groups", "data_items", "user_privileges")})

    groups = oauth2_get("oauth2/group/list").either(
        lambda err: {"groups_error": process_error(err)},
        lambda grp: {"groups": grp})
    roles = oauth2_get("oauth2/user/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})

    if request.method == "GET":
        return __render__(**{**groups, **roles})

    dataset_type = request.form["dataset_type"]
    offset = int(request.form.get("offset", 0))
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        flash("InvalidDatasetType: An invalid dataset type was provided",
              "alert-danger")
        return __render__(**{**groups, **roles})

    data_items = oauth2_get(
        f"oauth2/resource/{dataset_type}/ungrouped-data?offset={offset}").either(
            lambda err: {"data_items_error": process_error(err)},
            lambda data: {"data_items": data})
    return __render__(**{
        **groups, **roles, **data_items, "dataset_type": dataset_type,
            "offset": (offset if offset >= 100 else 0)
    })

@data.route("/link", methods=["POST"])
def link_data():
    """Link the selected data to a specific group."""
    def __error__(err, form_data):
        error = process_error(err)
        flash(f"{error['error']}: {error['error_description']}", "alert-danger")
        return redirect(url_for("oauth2.data.list_data", **form_data), code=307)
    def __success__(success, form_data):
        flash("Data successfully linked!", "alert-success")
        return redirect(url_for("oauth2.data.list_data", **form_data), code=307)

    form = request.form
    try:
        keys = ("dataset_id", "dataset_type", "group_id")
        assert all(item in form for item in keys)
        assert all(bool(form[item]) for item in keys)
        state_data = {
            "dataset_type": form["dataset_type"],
            "offset": form.get("offset", 0)}
        return oauth2_post(
            "oauth2/resource/data/link",
            data={
                "dataset_type": form["dataset_type"],
                "dataset_id": form["dataset_id"],
                "group_id": form["group_id"]
            }).either(lambda err: __error__(err, state_data),
                      lambda success: __success__(success, state_data))
    except AssertionError as aserr:
        flash("You must provide all the expected data.", "alert-error")
        return redirect(url_for("oauth2.data.list_data"))
