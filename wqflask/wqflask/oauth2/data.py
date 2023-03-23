"""Handle linking data to groups."""
from flask import (
    flash, request, url_for, redirect, Response, Blueprint, render_template)

from .request_utils import process_error
from .client import oauth2_get, oauth2_post

data = Blueprint("data", __name__)

def __render_template__(templatepath, **kwargs):
    roles = kwargs.get("roles", tuple())
    user_privileges = tuple(
        privilege["privilege_id"] for role in roles
        for privilege in role["privileges"])
    return render_template(
        templatepath, **kwargs, user_privileges=user_privileges)

@data.route("/<string:species_name>/<string:dataset_type>/list",
            methods=["GET", "POST"])
def list_data_by_species_and_dataset(
        species_name: str, dataset_type: str) -> Response:
    templates = {
        "mrna": "oauth2/data-list-mrna.html",
        "genotype": "oauth2/data-list-genotype.html",
        "phenotype": "oauth2/data-list-phenotype.html"}
    roles = oauth2_get("oauth2/user/roles").either(
        lambda err: {"roles_error": process_error(err)},
        lambda roles: {"roles": roles})
    per_page = int(request.args.get("per_page", 500))
    traits = oauth2_get(
        (f"search/?type={dataset_type}&per_page={per_page}&query="
         f"species:{species_name}")).either(
             lambda err: {"traits_error": process_error(er)},
             lambda trts: {"traits": tuple({
                 "index": idx, **trait
             } for idx, trait in enumerate(trts, start=1))})

    return __render_template__(
        templates[dataset_type], **roles, **traits, species_name=species_name,
        dataset_type=dataset_type, per_page=per_page,
        query=request.args.get("query", ""))

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
    species = oauth2_get("oauth2/data/species").either(
        lambda err: {"species_error": process_error(err)},
        lambda species: {"species": species})

    if request.method == "GET":
        return __render__(**{**groups, **roles, **species})

    species_name = request.form["species_name"]
    dataset_type = request.form["dataset_type"]
    if dataset_type not in ("mrna", "genotype", "phenotype"):
        flash("InvalidDatasetType: An invalid dataset type was provided",
              "alert-danger")
        return __render__(**{**groups, **roles, **species})

    return redirect(url_for(
        "oauth2.data.list_data_by_species_and_dataset",
        species_name=species_name, dataset_type=dataset_type))

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
        keys = ("dataset_type", "group_id")
        assert all(item in form for item in keys)
        assert all(bool(form[item]) for item in keys)
        state_data = {
            "dataset_type": form["dataset_type"],
            "offset": form.get("offset", 0)}
        dataset_ids = form.getlist("dataset_ids")
        if len(dataset_ids) == 0:
            flash("You must select at least one item to link", "alert-danger")
            return redirect(url_for(
                "oauth2.data.list_data", **state_data))
        return oauth2_post(
            "oauth2/group/data/link",
            data={
                "dataset_type": form["dataset_type"],
                "dataset_ids": dataset_ids,
                "group_id": form["group_id"]
            }).either(lambda err: __error__(err, state_data),
                      lambda success: __success__(success, state_data))
    except AssertionError as aserr:
        flash("You must provide all the expected data.", "alert-danger")
        return redirect(url_for("oauth2.data.list_data"))
