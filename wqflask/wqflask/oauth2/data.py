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

    def __process_menus__(mns):
        return {
            species_id: {
                "display_name": display_name,
                "family": family,
                "groups": {
                    group_id: {
                        "group_name": group_name,
                        "family": family,
                        "types": {
                            type_id: {
                                "menu_value": type_menu_value,
                                "menu_heading": type_menu_heading,
                                "datasets": tuple(
                                    dict(zip(("accession_id", "dataset_id",
                                              "dataset_fullname"),
                                             dataset_row))
                                    for dataset_row in mns["datasets"][
                                            species_id][group_id][type_id])
                            }
                            for type_id, type_menu_value, type_menu_heading
                            in mns["types"][species_id][group_id]
                        }
                    }
                    for group_id, group_name, family in mns["groups"][species_id]
                }
            }
            for species_id, display_name, family in mns["species"]}

    groups = oauth2_get("oauth2/group/list").either(
        lambda err: {"groups_error": process_error(err)},
        lambda grp: {"groups": grp})
    roles = oauth2_get("oauth2/user/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})
    menus = oauth2_get("menu/generate/json").either(
        lambda err: {"menus_error": process_error(err)},
        lambda mns: {"menus": __process_menus__(mns)})

    if request.method == "GET":
        return __render__(**{**groups, **roles, **menus})

    dataset_type = request.form["dataset_type"]
    offset = int(request.form.get("offset", 0)) + (
        0 if request.form.get("offset_submit") is None else(
            100 if request.form["offset_submit"] == "Next" else -100))
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        flash("InvalidDatasetType: An invalid dataset type was provided",
              "alert-danger")
        return __render__(**{**groups, **roles})

    data_items = oauth2_get(
        f"oauth2/group/{dataset_type}/ungrouped-data?offset={offset}").either(
            lambda err: {"data_items_error": process_error(err)},
            lambda data: {"data_items": data})
    return __render__(**{
        **groups, **roles, **menus, **data_items, "dataset_type": dataset_type,
            "offset": offset
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
            "oauth2/group/data/link",
            data={
                "dataset_type": form["dataset_type"],
                "dataset_id": form["dataset_id"],
                "group_id": form["group_id"]
            }).either(lambda err: __error__(err, state_data),
                      lambda success: __success__(success, state_data))
    except AssertionError as aserr:
        flash("You must provide all the expected data.", "alert-error")
        return redirect(url_for("oauth2.data.list_data"))
